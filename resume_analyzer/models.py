from django.db import models
from django.contrib.auth.models import User

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class ResumeAnalysis(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume_analysis')
    uploaded_file = models.FileField(upload_to='resumes/')
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name='resumes')
    extracted_by = models.CharField(max_length=10, default='Code', choices=[('AI', 'AI'), ('Code', 'Code')])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume Analysis for {self.user.username}"
