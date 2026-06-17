import os
import tempfile
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
    # Seed default HR questions if table is empty
    if not HRQuestion.objects.exists():
        for q_data in DEFAULT_HR_QUESTIONS:
            HRQuestion.objects.create(**q_data)

    questions = HRQuestion.objects.all()
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

@login_required
def hr_evaluate_view(request, question_id):
    if request.method == 'POST':
        question = get_object_or_404(HRQuestion, id=question_id)
        data = json.loads(request.body)
        user_answer = data.get('answer', '').strip()

        if not user_answer:
            return JsonResponse({'status': 'error', 'message': 'Answer cannot be empty.'}, status=400)

        # Keyword analyzer logic
        key_phrases = [kp.strip().lower() for kp in question.key_phrases.split(',') if kp.strip()]
        answer_lower = user_answer.lower()
        
        matched_phrases = []
        for kp in key_phrases:
            if kp in answer_lower:
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
            feedback_points.append(f"Good focus on relevant topics. You successfully incorporated key phrases: {', '.join(matched_phrases)}.")
        else:
            feedback_points.append("Your response lacks specific target vocabulary. Try integrating phrases relating to your direct experience, tools, and background.")

        if word_count < 25:
            feedback_points.append("Improve communication depth. Your response is quite brief. Aim for 3-5 sentences (at least 50 words) to properly explain your ideas.")
        elif word_count >= 100:
            feedback_points.append("Good answer depth. Be careful not to ramble; keep your response concise and structured.")
        else:
            feedback_points.append("Excellent communication length. Your response was concise and well-paced.")

        # Save or update attempt
        attempt, created = HRAttempt.objects.get_or_create(user=request.user, question=question)
        attempt.user_answer = user_answer
        attempt.feedback = "\n".join(feedback_points)
        attempt.score = score
        attempt.save()

        return JsonResponse({
            'status': 'success',
            'score': score,
            'feedback': attempt.feedback
        })
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
