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
        import os
        from django.conf import settings
        import urllib.request
        import json

        api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
        
        milestones_list = []
        if api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                prompt = (
                    f"Create a personalized 4-month learning roadmap for a candidate who wants to become a: '{career_goal}'.\n\n"
                    f"Return your response strictly as a JSON array containing exactly 4 objects (one for each month: Month 1, Month 2, Month 3, Month 4).\n"
                    f"Each object must have exactly these keys:\n"
                    f"- 'month': An integer (1, 2, 3, or 4)\n"
                    f"- 'topic': A short string representing the month's topic\n"
                    f"- 'description': A brief, 1-2 sentence description of what to learn and master during that month\n\n"
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
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    text_response = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    if text_response.startswith("```"):
                        lines = text_response.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        text_response = "\n".join(lines).strip()
                    
                    milestones_list = json.loads(text_response)
            except Exception as e:
                print(f"Gemini Roadmap generation failed: {str(e)}. Falling back to local templates.")

        if not milestones_list:
            milestones_list = ROADMAP_TEMPLATES.get(career_goal, [])
            if not milestones_list:
                milestones_list = [
                    {'month': 1, 'topic': f'Foundations of {career_goal}', 'description': f'Learn the fundamental concepts, basic tools, and initial setup required for a {career_goal}.'},
                    {'month': 2, 'topic': f'Intermediate concepts in {career_goal}', 'description': f'Build your first projects, learn best practices, and work with core frameworks.'},
                    {'month': 3, 'topic': f'Advanced topics in {career_goal}', 'description': f'Master advanced architecture, optimizations, and modern design patterns.'},
                    {'month': 4, 'topic': f'System Integration & Portfolio', 'description': f'Build a capstone project, deploy it, and prepare for interviews as a {career_goal}.'}
                ]

        for temp in milestones_list:
            Milestone.objects.create(
                roadmap=roadmap,
                month=temp.get('month', 1),
                topic=temp.get('topic', 'Topic'),
                description=temp.get('description', 'Description')
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
