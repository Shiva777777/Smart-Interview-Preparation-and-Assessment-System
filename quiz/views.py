import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from resume_analyzer.models import ResumeAnalysis, Skill
from .models import Question, QuizAttempt, UserAnswer

@login_required
def quiz_home_view(request):
    analysis = ResumeAnalysis.objects.filter(user=request.user).first()
    has_resume = analysis is not None
    detected_skills = list(analysis.skills.values_list('name', flat=True)) if has_resume else []
    
    # Dynamically compile domains: start with defaults, and add user's skills!
    default_domains = [choice[0] for choice in Question.DOMAIN_CHOICES]
    domains = list(default_domains)
    for skill in detected_skills:
        if skill not in domains:
            domains.append(skill)

    context = {
        'has_resume': has_resume,
        'detected_skills': detected_skills,
        'domains': domains,
        'difficulties': [choice[0] for choice in Question.DIFFICULTY_CHOICES],
    }
    return render(request, 'quiz/home.html', context)

@login_required
def manual_skill_select_view(request):
    # Retrieve all available skills to select from
    skills = Skill.objects.all()
    if request.method == 'POST':
        selected_skill_ids = request.POST.getlist('skills')
        if not selected_skill_ids:
            messages.error(request, "Please select at least one skill.")
            return redirect('manual_skill_select')
        
        # Store selected skills in session to generate quiz
        selected_skills = list(Skill.objects.filter(id__in=selected_skill_ids).values_list('name', flat=True))
        request.session['selected_quiz_skills'] = selected_skills
        return redirect('quiz_generate_from_skills')
        
    return render(request, 'quiz/manual_skills.html', {'skills': skills})

@login_required
def generate_personalized_quiz_view(request):
    # Determine skills: either from resume or session (manual)
    analysis = ResumeAnalysis.objects.filter(user=request.user).first()
    skills = []
    if analysis:
        skills = list(analysis.skills.values_list('name', flat=True))
    else:
        skills = request.session.get('selected_quiz_skills', [])

    if not skills:
        messages.warning(request, "Please upload a resume or select skills manually first.")
        return redirect('manual_skill_select')

    # Try to generate personalized quiz questions via Gemini first
    import os
    import urllib.request
    import json
    from django.conf import settings

    api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
    questions = None

    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
            prompt = (
                f"Generate exactly 10 multiple-choice questions for a candidate who has these skills: {skills}.\n"
                f"The questions should be relevant to these skills and professional domain. For each question, provide 4 options, a correct answer, and an explanation.\n\n"
                f"Return your response strictly as a JSON array where each object has these keys:\n"
                f"- 'domain': The specific skill or domain the question belongs to (string, must be one of: {skills})\n"
                f"- 'difficulty': Difficulty level (must be one of: 'Easy', 'Medium', 'Hard')\n"
                f"- 'text': The question text (string)\n"
                f"- 'option_a': Option A (string)\n"
                f"- 'option_b': Option B (string)\n"
                f"- 'option_c': Option C (string)\n"
                f"- 'option_d': Option D (string)\n"
                f"- 'correct_option': The correct option letter (must be one of: 'A', 'B', 'C', 'D')\n"
                f"- 'explanation': Explanation of the correct option (string)\n\n"
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
                
                generated_questions = json.loads(text_response)
                created_qs = []
                for q_data in generated_questions:
                    q_obj = Question.objects.create(
                        domain=q_data.get('domain', 'Personalized'),
                        difficulty=q_data.get('difficulty', 'Medium'),
                        text=q_data.get('text'),
                        option_a=q_data.get('option_a'),
                        option_b=q_data.get('option_b'),
                        option_c=q_data.get('option_c'),
                        option_d=q_data.get('option_d'),
                        correct_option=q_data.get('correct_option', 'A'),
                        explanation=q_data.get('explanation', '')
                    )
                    created_qs.append(q_obj)
                if created_qs:
                    questions = Question.objects.filter(id__in=[q.id for q in created_qs])
        except Exception as e:
            print(f"Gemini Personalized Quiz Generation failed: {str(e)}")

    if not questions or not questions.exists():
        # Fallback to local DB query mapping
        domain_mapping = {
            'Python': 'Python',
            'Django': 'Python',
            'MySQL': 'SQL',
            'Docker': 'DevOps',
            'AWS': 'DevOps',
            'Jenkins': 'DevOps',
            'Linux': 'Operating System',
            'Terraform': 'DevOps',
            'Kubernetes': 'DevOps',
            'SQL': 'SQL',
            'Machine Learning': 'Machine Learning',
            'Data Science': 'Machine Learning',
        }

        target_domains = set()
        for skill in skills:
            mapped = domain_mapping.get(skill)
            if mapped:
                target_domains.add(mapped)
            elif Question.objects.filter(domain=skill).exists():
                target_domains.add(skill)

        if not target_domains:
            target_domains = ['Python', 'SQL', 'DevOps']

        # Get 10 random questions across target domains
        questions = Question.objects.filter(domain__in=target_domains).order_by('?')[:10]
        
        if not questions.exists():
            questions = Question.objects.all().order_by('?')[:10]

    request.session['quiz_questions_ids'] = [q.id for q in questions]
    request.session['quiz_domain'] = "Personalized (Resume/Skills)"
    request.session['quiz_difficulty'] = "Mixed"
    
    return redirect('quiz_session')

@login_required
def start_quiz_session_view(request):
    if request.method == 'POST':
        domain = request.POST.get('domain')
        difficulty = request.POST.get('difficulty')
        count = int(request.POST.get('count', 10))

        # Query matching questions
        questions = Question.objects.filter(domain=domain, difficulty=difficulty).order_by('?')[:count]
        if not questions.exists():
            # Try setting back to any difficulty as fallback
            questions = Question.objects.filter(domain=domain).order_by('?')[:count]
            
        if not questions.exists():
            # Let's generate questions dynamically using Gemini!
            import os
            import urllib.request
            import json
            from django.conf import settings

            api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
            if api_key:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                    prompt = (
                        f"Generate exactly {count} multiple-choice questions for the domain/skill: '{domain}'.\n"
                        f"Difficulty level should be: '{difficulty}'. Each question must have 4 options, a correct answer, and an explanation.\n\n"
                        f"Return your response strictly as a JSON array where each object has these keys:\n"
                        f"- 'difficulty': Difficulty level (must be '{difficulty}')\n"
                        f"- 'text': The question text (string)\n"
                        f"- 'option_a': Option A (string)\n"
                        f"- 'option_b': Option B (string)\n"
                        f"- 'option_c': Option C (string)\n"
                        f"- 'option_d': Option D (string)\n"
                        f"- 'correct_option': The correct option letter (must be one of: 'A', 'B', 'C', 'D')\n"
                        f"- 'explanation': Explanation of the correct option (string)\n\n"
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
                        
                        generated_questions = json.loads(text_response)
                        created_qs = []
                        for q_data in generated_questions:
                            q_obj = Question.objects.create(
                                domain=domain,
                                difficulty=q_data.get('difficulty', difficulty),
                                text=q_data.get('text'),
                                option_a=q_data.get('option_a'),
                                option_b=q_data.get('option_b'),
                                option_c=q_data.get('option_c'),
                                option_d=q_data.get('option_d'),
                                correct_option=q_data.get('correct_option', 'A'),
                                explanation=q_data.get('explanation', '')
                            )
                            created_qs.append(q_obj)
                        if created_qs:
                            questions = Question.objects.filter(id__in=[q.id for q in created_qs])
                except Exception as e:
                    print(f"Gemini Quiz Generation failed: {str(e)}")

        if not questions.exists():
            messages.error(request, f"No questions found for domain: {domain} and failed to generate via AI.")
            return redirect('quiz_home')
        
        request.session['quiz_questions_ids'] = [q.id for q in questions]
        request.session['quiz_domain'] = domain
        request.session['quiz_difficulty'] = difficulty
        return redirect('quiz_session')
    
    return redirect('quiz_home')

@login_required
def quiz_session_view(request):
    question_ids = request.session.get('quiz_questions_ids', [])
    if not question_ids:
        messages.error(request, "No active quiz session found.")
        return redirect('quiz_home')

    questions_qs = Question.objects.filter(id__in=question_ids)
    # Maintain the session random order
    questions_list = sorted(list(questions_qs), key=lambda q: question_ids.index(q.id))

    # Serialize questions for frontend JS execution
    serialized_questions = []
    for q in questions_list:
        serialized_questions.append({
            'id': q.id,
            'text': q.text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
        })

    context = {
        'questions_json': json.dumps(serialized_questions),
        'domain': request.session.get('quiz_domain', 'Quiz'),
        'difficulty': request.session.get('quiz_difficulty', 'Mixed'),
        'total_questions': len(serialized_questions),
    }
    return render(request, 'quiz/session.html', context)

@login_required
def quiz_submit_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            answers = data.get('answers', {})  # Dict mapping Question ID (str) to selected option ('A', 'B', 'C', 'D' or null)
            tab_switches = int(data.get('tab_switches', 0))
            window_minimizes = int(data.get('window_minimizes', 0))
            focus_lost = int(data.get('focus_lost', 0))

            question_ids = request.session.get('quiz_questions_ids', [])
            if not question_ids:
                return JsonResponse({'status': 'error', 'message': 'Session expired'}, status=400)

            questions = Question.objects.filter(id__in=question_ids)
            
            # Score calculations
            score_correct = 0
            user_answers_to_create = []

            for q in questions:
                user_ans = answers.get(str(q.id))
                is_correct = (user_ans == q.correct_option)
                if is_correct:
                    score_correct += 1

                user_answers_to_create.append(UserAnswer(
                    question=q,
                    selected_option=user_ans,
                    is_correct=is_correct
                ))

            # Calculate final percentage
            total_questions = len(question_ids)
            final_percentage = int((score_correct / total_questions) * 100) if total_questions > 0 else 0

            # Create attempt record
            attempt = QuizAttempt.objects.create(
                user=request.user,
                domain=request.session.get('quiz_domain', 'Quiz'),
                difficulty=request.session.get('quiz_difficulty', 'Mixed'),
                score=final_percentage,
                total_questions=total_questions,
                tab_switches=tab_switches,
                window_minimizes=window_minimizes,
                focus_lost=focus_lost
            )

            # Link answers to attempt
            for ua in user_answers_to_create:
                ua.attempt = attempt
                ua.save()

            # Clean session
            if 'quiz_questions_ids' in request.session: del request.session['quiz_questions_ids']
            if 'quiz_domain' in request.session: del request.session['quiz_domain']
            if 'quiz_difficulty' in request.session: del request.session['quiz_difficulty']

            return JsonResponse({'status': 'success', 'redirect_url': f'/quiz/result/{attempt.id}/'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return redirect('quiz_home')

@login_required
def quiz_result_view(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    answers = attempt.answers.all().select_related('question')
    
    # Calculate totals
    correct_count = answers.filter(is_correct=True).count()
    wrong_count = answers.count() - correct_count

    context = {
        'attempt': attempt,
        'answers': answers,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'is_eligible_for_cert': attempt.score >= 70,
    }
    return render(request, 'quiz/result.html', context)
