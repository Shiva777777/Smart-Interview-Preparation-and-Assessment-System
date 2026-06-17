from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from accounts.models import UserProfile
from .models import RoadmapProgress, Milestone

ROADMAP_TEMPLATES = {
    'DevOps Engineer': [
        {'month': 1, 'topic': 'Linux & Git basics', 'description': 'Learn Linux command line scripting, file structures, cron jobs, and basic Git versioning workflows (branching, merging).'},
        {'month': 2, 'topic': 'Containerization & Build CI', 'description': 'Learn Docker (containers, images, volumes) and Jenkins (pipelines, automated testing, builds).'},
        {'month': 3, 'topic': 'Cloud & Infrastructure as Code', 'description': 'Learn AWS Cloud Services (EC2, S3, IAM, VPC) and Terraform scripting for provisioning resources.'},
        {'month': 4, 'topic': 'Container Orchestration', 'description': 'Learn Kubernetes clusters, pods configurations, service models, and Helm packages management.'}
    ],
    'Backend Developer': [
        {'month': 1, 'topic': 'Advanced Python & Data Structures', 'description': 'Master OOP concepts, lists, dicts, tuples, time complexity analysis, and algorithms.'},
        {'month': 2, 'topic': 'Django Framework Basics', 'description': 'Learn Django MTV architecture, URL routing, generic views, form processing, and model migrations.'},
        {'month': 3, 'topic': 'Database Design & SQL Optimization', 'description': 'Master database schema normalization, indexing, outer joins, raw SQL aggregates, and Django ORM optimization.'},
        {'month': 4, 'topic': 'REST APIs & Production Deployment', 'description': 'Learn Django REST Framework (DRF) serializers, CORS headers, Docker containers wrapper, and Gunicorn/Nginx setup.'}
    ],
    'Data Scientist': [
        {'month': 1, 'topic': 'Python Data Wrangling', 'description': 'Master NumPy matrix operations, Pandas DataFrame processing, cleaning missing data, and Matplotlib/Seaborn visualization.'},
        {'month': 2, 'topic': 'Applied Math & Statistics', 'description': 'Learn linear algebra, calculus, descriptive statistics, probability distributions, and hypothesis testing.'},
        {'month': 3, 'topic': 'Machine Learning Algorithms', 'description': 'Master Scikit-Learn regression, classification models, Decision Trees, Random Forests, and model tuning metrics (F1-score, ROC-AUC).'},
        {'month': 4, 'topic': 'Deep Learning & API Deployment', 'description': 'Learn Neural Network architectures with PyTorch/TensorFlow, and deploy models using Flask or FastAPI endpoints.'}
    ]
}

@login_required
def roadmap_view(request):
    profile = request.user.profile
    career_goal = profile.career_goal

    if not career_goal:
        messages.warning(request, "Please set a Career Goal in your Profile first.")
        return redirect('profile')

    roadmap, created = RoadmapProgress.objects.get_or_create(user=request.user, defaults={'goal': career_goal})
    
    # If the goal has changed, reset the roadmap
    if roadmap.goal != career_goal:
        roadmap.milestones.all().delete()
        roadmap.goal = career_goal
        roadmap.save()
        created = True

    if created or not roadmap.milestones.exists():
        templates = ROADMAP_TEMPLATES.get(career_goal, [])
        for temp in templates:
            Milestone.objects.create(
                roadmap=roadmap,
                month=temp['month'],
                topic=temp['topic'],
                description=temp['description']
            )

    milestones = roadmap.milestones.all().order_by('month')
    
    return render(request, 'roadmap/display.html', {
        'roadmap': roadmap,
        'milestones': milestones,
        'career_goal': career_goal
    })

@login_required
def toggle_milestone_view(request, milestone_id):
    if request.method == 'POST':
        milestone = get_object_or_404(Milestone, id=milestone_id, roadmap__user=request.user)
        milestone.completed = not milestone.completed
        milestone.save()
        return JsonResponse({'status': 'success', 'completed': milestone.completed})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
