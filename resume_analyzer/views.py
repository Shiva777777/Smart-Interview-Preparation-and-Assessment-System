from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ResumeAnalysis, Skill
from .utils import extract_text_from_pdf, extract_text_from_docx, parse_resume_text

DEFAULT_SKILLS = [
    'Python', 'Django', 'Docker', 'AWS', 'Jenkins', 'Linux', 
    'Terraform', 'Kubernetes', 'MySQL', 'Git', 'Java', 'C++', 
    'JavaScript', 'HTML', 'CSS', 'React', 'DevOps', 'SQL', 
    'Machine Learning', 'Data Science', 'NLTK', 'scikit-learn'
]

@login_required
def resume_upload_view(request):
    # Ensure default skills are present in database
    for skill_name in DEFAULT_SKILLS:
        Skill.objects.get_or_create(name=skill_name)
    
    analysis = ResumeAnalysis.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        uploaded_file = request.FILES.get('resume')
        if not uploaded_file:
            messages.error(request, "Please select a file to upload.")
            return redirect('resume_upload')
            
        file_name = uploaded_file.name.lower()
        if not (file_name.endswith('.pdf') or file_name.endswith('.docx')):
            messages.error(request, "Unsupported file format. Please upload a PDF or DOCX file.")
            return redirect('resume_upload')

        # Read file text
        if file_name.endswith('.pdf'):
            text = extract_text_from_pdf(uploaded_file)
        else:
            text = extract_text_from_docx(uploaded_file)

        # Parse text details
        import os
        from django.conf import settings
        api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
        master_skills = list(Skill.objects.values_list('name', flat=True))
        parsed = parse_resume_text(text, master_skills, api_key=api_key)

        # Create or update database record
        if not analysis:
            analysis = ResumeAnalysis(user=request.user)
        
        analysis.uploaded_file = uploaded_file
        analysis.name = parsed['name'] or request.user.get_full_name() or request.user.username
        analysis.email = parsed['email'] or request.user.email
        analysis.phone = parsed['phone']
        analysis.education = parsed['education']
        analysis.certifications = parsed['certifications']
        analysis.save()

        # Update parsed skills ManyToMany
        analysis.skills.clear()
        for skill_name in parsed['skills']:
            skill_obj = Skill.objects.get(name=skill_name)
            analysis.skills.add(skill_obj)
        
        messages.success(request, "Resume parsed and analyzed successfully!")
        return redirect('resume_result')

    return render(request, 'resume_analyzer/upload.html', {'analysis': analysis})

@login_required
def resume_result_view(request):
    analysis = ResumeAnalysis.objects.filter(user=request.user).first()
    if not analysis:
        messages.warning(request, "No resume has been uploaded yet.")
        return redirect('resume_upload')
    
    return render(request, 'resume_analyzer/result.html', {'analysis': analysis})
