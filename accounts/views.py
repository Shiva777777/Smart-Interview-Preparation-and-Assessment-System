import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Avg, Max
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile

# Import other apps' models dynamically to avoid circular import issues
def get_dashboard_data(user):
    from resume_analyzer.models import ResumeAnalysis
    from quiz.models import QuizAttempt
    from coding.models import CodingAttempt
    from hr_interview.models import HRAttempt
    from roadmap.models import RoadmapProgress

    # Resume status
    resume = ResumeAnalysis.objects.filter(user=user).first()
    resume_status = "Uploaded" if resume else "Not Uploaded"
    detected_skills = list(resume.skills.values_list('name', flat=True)) if resume else []

    # Quiz stats
    quiz_attempts = QuizAttempt.objects.filter(user=user)
    total_quizzes = quiz_attempts.count()
    avg_score = quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0
    max_score = quiz_attempts.aggregate(Max('score'))['score__max'] or 0

    # Coding stats
    coding_attempts = CodingAttempt.objects.filter(user=user)
    total_coding = coding_attempts.count()

    # HR stats
    hr_attempts = HRAttempt.objects.filter(user=user)
    total_hr = hr_attempts.count()

    # Strength & Weakness calculation based on categories
    default_categories = ['Python', 'DBMS', 'Operating System', 'Computer Networks', 'DevOps', 'SQL', 'Machine Learning']
    attempted_domains = list(quiz_attempts.values_list('domain', flat=True).distinct())
    categories = list(set(default_categories + attempted_domains + detected_skills))

    domain_scores = {}
    for cat in categories:
        cat_avg = quiz_attempts.filter(domain=cat).aggregate(Avg('score'))['score__avg']
        if cat_avg is not None:
            domain_scores[cat] = float(cat_avg)

    strong_subjects = [cat for cat, score in domain_scores.items() if score >= 70]
    weak_subjects = [cat for cat, score in domain_scores.items() if score < 50]

    # Chart 1: Performance over time (line chart)
    attempts_history = list(quiz_attempts.order_by('completed_at')[:10].values('completed_at', 'score'))
    history_labels = [att['completed_at'].strftime('%m-%d') for att in attempts_history]
    history_scores = [float(att['score']) for att in attempts_history]

    # Chart 2: Domain score breakdown (radar/bar)
    domain_labels = list(domain_scores.keys())
    domain_values = list(domain_scores.values())
    if not domain_labels:
        domain_labels = default_categories
        domain_values = [0.0] * len(default_categories)

    # Roadmap progress
    roadmap = RoadmapProgress.objects.filter(user=user).first()
    roadmap_progress = 0
    if roadmap:
        total_items = roadmap.milestones.count()
        completed_items = roadmap.milestones.filter(completed=True).count()
        roadmap_progress = int((completed_items / total_items) * 100) if total_items > 0 else 0

    return {
        'resume_status': resume_status,
        'detected_skills': detected_skills,
        'total_quizzes': total_quizzes,
        'total_coding': total_coding,
        'total_hr': total_hr,
        'avg_score': round(avg_score, 1),
        'max_score': round(max_score, 1),
        'strong_subjects': strong_subjects or ["None yet"],
        'weak_subjects': weak_subjects or ["None yet"],
        'history_labels': json.dumps(history_labels),
        'history_scores': json.dumps(history_scores),
        'domain_labels': json.dumps(domain_labels),
        'domain_values': json.dumps(domain_values),
        'roadmap_progress': roadmap_progress,
        'career_goal': user.profile.career_goal or "Not Selected",
    }

@login_required
def dashboard_view(request):
    data = get_dashboard_data(request.user)
    return render(request, 'dashboard.html', data)

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Save profile extra details
            profile = user.profile
            profile.phone_number = form.cleaned_data.get('phone_number')
            profile.preferred_domain = form.cleaned_data.get('preferred_domain')
            profile.career_goal = form.cleaned_data.get('career_goal')
            profile.save()
            
            messages.success(request, f"Account created successfully for {user.username}! You can now login.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        pwd_form = PasswordChangeForm(request.user, request.POST)
        
        # Check which form is being submitted
        if 'update_profile' in request.POST:
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, "Your profile has been updated!")
                return redirect('profile')
        elif 'change_password' in request.POST:
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in after password change
                messages.success(request, "Your password was successfully updated!")
                return redirect('profile')
            else:
                messages.error(request, "Please correct the errors below.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        pwd_form = PasswordChangeForm(request.user)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'pwd_form': pwd_form
    }
    return render(request, 'accounts/profile.html', context)
