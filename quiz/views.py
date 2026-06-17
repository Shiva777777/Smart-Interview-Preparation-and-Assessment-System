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
    
    context = {
        'has_resume': has_resume,
        'detected_skills': detected_skills,
        'domains': [choice[0] for choice in Question.DOMAIN_CHOICES],
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

    # Query questions that match the skills/domains
    # Map typical resume skills to quiz domains
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
        # Fallback to random if no exact matches
        target_domains = ['Python', 'SQL', 'DevOps']

    # Get 10 random questions across target domains
    questions = Question.objects.filter(domain__in=target_domains).order_by('?')[:10]
    
    if not questions.exists():
        # absolute fallback
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
                messages.error(request, f"No questions found for domain: {domain}.")
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
