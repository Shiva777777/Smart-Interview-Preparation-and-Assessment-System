import os
import tempfile
import re
import urllib.request
import urllib.error
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import json
from gtts import gTTS
import speech_recognition as sr
from .models import HRQuestion, HRAttempt

# Default HR questions
DEFAULT_HR_QUESTIONS = [
    {
        'text': 'Tell me about yourself.',
        'key_phrases': 'experience, project, graduate, study, skills, focus, background',
        'explanation': 'Give a brief walkthrough of your education, projects, key technical skills, and current career trajectory. Keep it under 2 minutes.'
    },
    {
        'text': 'Why should we hire you?',
        'key_phrases': 'skills, fit, value, contribution, team, goal, learn, solve',
        'explanation': 'Align your technical skills and attitude with the job description. Emphasize how your background adds value and how quickly you can contribute.'
    },
    {
        'text': 'What are your strengths and weaknesses?',
        'key_phrases': 'strength, weakness, improve, learn, patient, detail, focus',
        'explanation': 'For strengths, list something concrete (e.g., fast learner). For weaknesses, name an actual minor weakness but show what active steps you are taking to overcome it.'
    },
    {
        'text': 'Describe a challenging situation and how you overcame it.',
        'key_phrases': 'challenge, situation, resolve, team, problem, leader, action, outcome',
        'explanation': 'Use the STAR method (Situation, Task, Action, Result). Highlight how you analyzed the issue and worked with others to solve it.'
    }
]

@login_required
def hr_home_view(request):
    from resume_analyzer.models import ResumeAnalysis
    analysis = ResumeAnalysis.objects.filter(user=request.user).first()

    if analysis:
        # User has uploaded a resume, get or generate custom questions
        questions = HRQuestion.objects.filter(user=request.user)
        if not questions.exists():
            api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
            generated_list = []
            
            career_goal = request.user.profile.career_goal or "Professional"
            preferred_domain = request.user.profile.preferred_domain or "General"
            skills = list(analysis.skills.values_list('name', flat=True))
            skills_str = ", ".join(skills)

            if api_key:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                    prompt = (
                        f"You are an expert interviewer. Generate exactly 5 personalized interview questions for a candidate with the following resume profile:\n"
                        f"- Name: {analysis.name}\n"
                        f"- Career Goal: {career_goal}\n"
                        f"- Preferred Domain: {preferred_domain}\n"
                        f"- Skills: {skills}\n"
                        f"- Education: {analysis.education}\n"
                        f"- Certifications: {analysis.certifications}\n\n"
                        f"The questions must be highly tailored to their specific background, field (whether it is B.Tech, MBA, Law, B.Com, Arts, or any other field), and skills. "
                        f"Include a mix of behavioral questions (e.g., about their projects, education or case studies) and conceptual/technical questions relevant to their field. "
                        f"For each question, provide 4-6 key phrases/keywords that a good answer should contain, and a detailed explanation of what the interviewer is looking for in a perfect response.\n\n"
                        f"Return your response strictly as a JSON array where each object has these keys:\n"
                        f"- 'text': The question text (string)\n"
                        f"- 'key_phrases': Comma-separated keywords/phrases to search for (string)\n"
                        f"- 'explanation': Tips and best practices on how to answer the question (string)\n\n"
                        f"Return ONLY the raw JSON array, without any markdown formatting or backticks."
                    )
                    data = {
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }]
                    }
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(data).encode('utf-8'),
                        headers={
                            'Content-Type': 'application/json',
                            'x-goog-api-key': api_key
                        },
                        method='POST'
                    )
                    with urllib.request.urlopen(req, timeout=20) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        text_response = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        if text_response.startswith("```"):
                            lines = text_response.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            text_response = "\n".join(lines).strip()
                        
                        generated_list = json.loads(text_response)
                except Exception as e:
                    print(f"Gemini Custom HR Interview Questions Generation failed: {str(e)}")

            if not generated_list:
                # Fallback to local templates
                fallback_skills = skills_str if skills_str else "your background and achievements"
                generated_list = [
                    {
                        'text': f'Tell me about your background and how your skills in {fallback_skills[:100]} prepare you for a role as a {career_goal}.',
                        'key_phrases': 'experience, skills, goal, background, learn',
                        'explanation': f'Walk through your education and how your skills align directly with the role of a {career_goal}.'
                    },
                    {
                        'text': f'Describe a major project or academic achievement where you applied {skills[0] if skills else "your domain knowledge"}. What was the outcome?',
                        'key_phrases': 'project, achievement, applied, outcome, challenge',
                        'explanation': 'Use the STAR method to describe the task, action you took, and final result.'
                    },
                    {
                        'text': f'Why are you interested in pursuing a career as a {career_goal}, and where do you see yourself in 3 years?',
                        'key_phrases': 'future, career, interest, learn, grow',
                        'explanation': 'Show your passion for the domain and how you plan to gain expertise and contribute to the field.'
                    },
                    {
                        'text': f'How do you handle working in a team or collaborating with others to solve a complex problem?',
                        'key_phrases': 'team, collaborate, communication, solution, solve',
                        'explanation': 'Give an example of a time you resolved a conflict or worked closely with teammates to deliver a project.'
                    }
                ]

            for q_data in generated_list:
                HRQuestion.objects.create(
                    user=request.user,
                    text=q_data.get('text', 'Interview Question'),
                    key_phrases=q_data.get('key_phrases', 'skills, experience'),
                    explanation=q_data.get('explanation', 'Explain your thoughts clearly.')
                )
            
            questions = HRQuestion.objects.filter(user=request.user)

    else:
        # Fallback to general HR questions if no resume uploaded
        questions = HRQuestion.objects.filter(user=None)
        if not questions.exists():
            for q_data in DEFAULT_HR_QUESTIONS:
                HRQuestion.objects.create(user=None, **q_data)
            questions = HRQuestion.objects.filter(user=None)

    user_attempts = HRAttempt.objects.filter(user=request.user)
    completed_q_ids = set(user_attempts.values_list('question_id', flat=True))

    return render(request, 'hr_interview/home.html', {
        'questions': questions,
        'completed_q_ids': completed_q_ids
    })

@login_required
def hr_session_view(request, question_id):
    question = get_object_or_404(HRQuestion, id=question_id)
    attempt = HRAttempt.objects.filter(user=request.user, question=question).first()
    return render(request, 'hr_interview/session.html', {
        'question': question,
        'attempt': attempt
    })

@login_required
def hr_tts_view(request, question_id):
    """Text to speech generation view using gTTS."""
    question = get_object_or_404(HRQuestion, id=question_id)
    
    # Ensure directory exists
    tts_dir = os.path.join(settings.MEDIA_ROOT, 'tts')
    os.makedirs(tts_dir, exist_ok=True)
    
    file_path = os.path.join(tts_dir, f'q_{question_id}.mp3')
    
    if not os.path.exists(file_path):
        try:
            tts = gTTS(text=question.text, lang='en')
            tts.save(file_path)
        except Exception as e:
            return HttpResponse(f"TTS Error: {str(e)}", status=500)
            
    try:
        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='audio/mp3')
    except Exception as e:
        return HttpResponse(f"File Read Error: {str(e)}", status=500)

@login_required
def hr_stt_view(request):
    """Speech to Text transcription using speech_recognition."""
    if request.method == 'POST' and request.FILES.get('audio_data'):
        audio_file = request.FILES['audio_data']
        
        # Save file to a temporary location
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav', dir=os.getcwd())
        try:
            with os.fdopen(temp_fd, 'wb') as f:
                for chunk in audio_file.chunks():
                    f.write(chunk)
            
            # Setup Speech Recognizer
            r = sr.Recognizer()
            with sr.AudioFile(temp_path) as source:
                # Adjust for noise if necessary
                r.adjust_for_ambient_noise(source)
                audio = r.record(source)
                
            text = r.recognize_google(audio)
            return JsonResponse({'status': 'success', 'transcript': text})
        except sr.UnknownValueError:
            return JsonResponse({'status': 'error', 'message': "Google Speech Recognition could not understand the audio. Please speak clearly or type your response."})
        except sr.RequestError as e:
            return JsonResponse({'status': 'error', 'message': f"Google STT service is unavailable: {str(e)}. Please type your response."})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Audio reading error: {str(e)}. Please write your response manually."})
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
                    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# Helper dictionary of synonyms/related terms for key interview concepts
SYNONYM_MAP = {
    'experience': ['experienced', 'work', 'career', 'job', 'history', 'position', 'internship', 'intern', 'roles', 'role'],
    'project': ['projects', 'build', 'task', 'assignment', 'system', 'application', 'app', 'module', 'develop', 'developed'],
    'graduate': ['graduated', 'degree', 'btech', 'mtech', 'bsc', 'engineering', 'college', 'university', 'institute', 'pursuing', 'pursue', 'studied', 'study'],
    'study': ['studying', 'study', 'learn', 'academic', 'education', 'student', 'pursue', 'pursuing', 'btech', 'mtech', 'degree'],
    'skills': ['skill', 'expertise', 'proficient', 'languages', 'stack', 'technology', 'technologies', 'knowledge', 'coding', 'programming'],
    'focus': ['focused', 'interest', 'specialize', 'specializing', 'major', 'aim', 'goal', 'passionate'],
    'background': ['profile', 'background', 'qualification', 'qualifications'],
    'fit': ['fitting', 'suitable', 'align', 'matches', 'match', 'compatibility', 'suited'],
    'value': ['benefit', 'asset', 'positive', 'growth', 'help', 'add', 'contribute'],
    'contribution': ['contribute', 'grow', 'impact', 'work', 'deliver', 'support', 'value'],
    'team': ['collaboration', 'collaborate', 'team', 'members', 'together', 'group', 'colleague', 'colleagues', 'coworker', 'coworkers'],
    'goal': ['goals', 'target', 'objective', 'career', 'future', 'aspiration'],
    'learn': ['learning', 'learn', 'adapt', 'growth', 'quick', 'understand', 'upgrade'],
    'solve': ['solving', 'solve', 'resolve', 'fix', 'tackle', 'handled', 'handle', 'overcame', 'overcome'],
    'strength': ['strengths', 'strong', 'skill', 'skills', 'benefit', 'positive', 'advantage', 'ability', 'abilities'],
    'weakness': ['weaknesses', 'weak', 'challenge', 'improve', 'limitation', 'shortcoming', 'struggle'],
    'improve': ['improving', 'growth', 'learn', 'learning', 'progress', 'better', 'overcome', 'working on'],
    'patient': ['patience', 'calm', 'listen', 'understanding', 'composed'],
    'detail': ['details', 'detail-oriented', 'analytical', 'thorough', 'organized'],
    'challenge': ['challenging', 'difficult', 'difficulty', 'struggle', 'issue', 'conflict', 'problem', 'obstacle'],
    'situation': ['incident', 'scenario', 'task', 'project', 'time', 'context', 'event', 'case'],
    'resolve': ['resolving', 'solved', 'solve', 'fix', 'fixed', 'overcame', 'overcome', 'handle', 'handled', 'remedy'],
    'problem': ['bug', 'issue', 'error', 'barrier', 'hurdle', 'trouble', 'difficulty'],
    'leader': ['leadership', 'lead', 'led', 'take charge', 'taking charge', 'manage', 'managed', 'guide', 'guided'],
    'action': ['step', 'steps', 'did', 'act', 'process', 'approach', 'solution'],
    'outcome': ['result', 'results', 'successfully', 'resolved', 'completed', 'ended', 'conclusion', 'finally']
}

try:
    from nltk.stem import PorterStemmer
    stemmer = PorterStemmer()
except ImportError:
    stemmer = None

def clean_and_tokenize(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return words

def match_phrase(kp, answer_words, answer_text_lower):
    # Direct substring match
    if kp in answer_text_lower:
        return True
        
    # Split the key phrase into words
    kp_words = clean_and_tokenize(kp)
    if not kp_words:
        return False
        
    # Check if all words in the key phrase (or their synonyms/stems) are found in the answer
    for kw in kp_words:
        synonyms = SYNONYM_MAP.get(kw, [])
        found_kw = False
        
        # Check direct word match or synonym match
        if kw in answer_words:
            found_kw = True
        else:
            for syn in synonyms:
                if syn in answer_words:
                    found_kw = True
                    break
                    
        # If not found yet, try stemming
        if not found_kw and stemmer:
            try:
                kw_stem = stemmer.stem(kw)
                for aw in answer_words:
                    if stemmer.stem(aw) == kw_stem:
                        found_kw = True
                        break
            except Exception:
                pass
                
        if not found_kw:
            return False
            
    return True

def evaluate_with_gemini(question_text, user_answer, api_key):
    prompt = (
        f"You are an expert HR interviewer evaluating a candidate's answer.\n"
        f"Question Asked: {question_text}\n"
        f"Candidate's Answer: {user_answer}\n\n"
        f"CRITICAL RELEVANCE AND ACCURACY RULES (MUST FOLLOW):\n"
        f"1. Directly Address the Question: The Candidate's Answer must directly answer the specific Question Asked ('{question_text}').\n"
        f"2. Strict Question/Answer Alignment: Verify that the candidate is not answering a different question. For example, if asked '{question_text}' but the candidate answers a completely different interview question (e.g. answering 'Why should we hire you' when asked 'Tell me about yourself', or answering with general technical skills instead of explaining a specific situation requested), this is a major failure.\n"
        f"3. Check for Correctness: If the question requires a specific explanation or factual description, check if the candidate's response is accurate and actually answers the core query. If the answer is vague, general filler, or completely off-topic, it must be failed.\n"
        f"4. Penalty: If the answer violates any of the rules above (is irrelevant, off-topic, answers a different question, is gibberish, or is factually incorrect), you MUST immediately fail the answer. You MUST set the 'score' strictly between 10 and 20, and the first bullet point in 'feedback' MUST explicitly start with: '❌ Irrelevant Answer: ...' or '❌ Incorrect Answer: ...' explaining exactly why the answer does not address the question asked.\n\n"
        f"EVALUATION CRITERIA (Only if the answer is relevant and correct):\n"
        f"Evaluate the answer based on: relevance, communication clarity, professionalism, and depth (score range: 50 to 100).\n\n"
        f"RESPONSE FORMAT:\n"
        f"Return ONLY a raw JSON object (no markdown backticks, no code block markers) with exactly two keys:\n"
        f"- 'score': an integer from 10 to 100\n"
        f"- 'feedback': a string containing 2-4 bulleted feedback points, each on a new line starting with '-' or '*'"
    )
    
    import time
    
    # Models to try in order of preference
    models = [
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-flash-latest"
    ]
    
    last_error = None
    error_details = []
    
    for model in models:
        for api_version in ["v1beta", "v1"]:
            url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={api_key}"
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            for attempt in range(2):
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(data).encode('utf-8'),
                        headers={
                            'Content-Type': 'application/json',
                            'x-goog-api-key': api_key
                        },
                        method='POST'
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        text_response = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        # Clean possible markdown block markers
                        if text_response.startswith("```"):
                            lines = text_response.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            text_response = "\n".join(lines).strip()
                        
                        result = json.loads(text_response)
                        score = int(result.get('score', 50))
                        feedback = result.get('feedback', '').strip()
                        return score, feedback, None
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    error_body = ""
                    if hasattr(e, 'read'):
                        try:
                            error_body = e.read().decode('utf-8')
                            error_msg += " - " + error_body
                        except:
                            pass
                    
                    error_details.append(f"Model: {model}, Version: {api_version}, Attempt: {attempt + 1}, Error: {error_msg}")
                    
                    # If 404, 400, or 403, don't retry, try next model/version
                    if "404" in error_msg or "400" in error_msg or "403" in error_msg:
                        break
                    # If 429, don't retry, try next model
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_body:
                        break
                    
                    # Transient error, wait and retry
                    time.sleep(1)
                    
    # If all failed, log details and return the error
    models_debug = ""
    try:
        debug_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req_debug = urllib.request.Request(debug_url, headers={'x-goog-api-key': api_key})
        with urllib.request.urlopen(req_debug, timeout=5) as resp_debug:
            models_debug = resp_debug.read().decode('utf-8')
    except Exception as list_err:
        models_debug = f"Failed to list models: {str(list_err)}"
        if hasattr(list_err, 'read'):
            try:
                models_debug += " - " + list_err.read().decode('utf-8')
            except:
                pass

    try:
        with open('api_test_debug.txt', 'w') as f:
            f.write("=== Diagnostic Log ===\n")
            f.write("\n".join(error_details))
            f.write(f"\n\nModels List Response: {models_debug}\n")
    except Exception as file_err:
        print(f"Failed to write debug file: {file_err}")
        
    return None, None, str(last_error)

@login_required
def hr_evaluate_view(request, question_id):
    try:
        if request.method == 'POST':
            question = get_object_or_404(HRQuestion, id=question_id)
            data = json.loads(request.body)
            user_answer = data.get('answer', '').strip()

            if not user_answer:
                return JsonResponse({'status': 'error', 'message': 'Answer cannot be empty.'}, status=400)

            # Get API key from environment or settings
            api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
            score = None
            feedback = None
            gemini_error = None
            evaluator_type = 'local'

            if api_key:
                score, feedback, gemini_error = evaluate_with_gemini(question.text, user_answer, api_key)
                if score is not None and feedback is not None:
                    evaluator_type = 'gemini'

            # Fallback to local analyzer if API key is not present or failed
            if score is None or feedback is None:
                evaluator_type = 'local'
                # Keyword analyzer logic using synonyms & stemming
                key_phrases = [kp.strip().lower() for kp in question.key_phrases.split(',') if kp.strip()]
                answer_lower = user_answer.lower()
                answer_words = clean_and_tokenize(user_answer)
                
                matched_phrases = []
                for kp in key_phrases:
                    if match_phrase(kp, answer_words, answer_lower):
                        matched_phrases.append(kp)

                # Calculate score metric
                total_phrases = len(key_phrases)
                match_ratio = len(matched_phrases) / total_phrases if total_phrases > 0 else 0
                
                # Adjust score for length
                word_count = len(user_answer.split())
                length_penalty = 1.0
                if word_count < 15:
                    length_penalty = 0.3
                elif word_count < 40:
                    length_penalty = 0.7
                    
                score = int((match_ratio * 100) * length_penalty)
                score = min(max(score, 10), 100) # Keep between 10% and 100%

                # Generate structured feedback
                feedback_points = []
                if len(matched_phrases) > 0:
                    feedback_points.append(f"Good focus on relevant topics. You successfully incorporated key concepts: {', '.join(matched_phrases)}.")
                else:
                    feedback_points.append("Your response lacks specific target vocabulary. Try integrating phrases relating to your direct experience, tools, and background.")

                if word_count < 25:
                    feedback_points.append("Improve communication depth. Your response is quite brief. Aim for 3-5 sentences (at least 50 words) to properly explain your ideas.")
                elif word_count >= 100:
                    feedback_points.append("Good answer depth. Be careful not to ramble; keep your response concise and structured.")
                else:
                    feedback_points.append("Excellent communication length. Your response was concise and well-paced.")
                    
                feedback = "\n".join(feedback_points)

            # Save or update attempt
            attempt, created = HRAttempt.objects.get_or_create(
                user=request.user,
                question=question,
                defaults={
                    'user_answer': user_answer,
                    'feedback': feedback,
                    'score': score
                }
            )
            if not created:
                attempt.user_answer = user_answer
                attempt.feedback = feedback
                attempt.score = score
                attempt.save()

            return JsonResponse({
                'status': 'success',
                'score': score,
                'feedback': attempt.feedback,
                'evaluator': evaluator_type,
                'evaluator_error': gemini_error
            })
            
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'Server Error: {str(e)}'})
