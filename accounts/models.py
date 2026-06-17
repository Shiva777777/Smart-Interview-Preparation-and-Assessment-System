from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    preferred_domain = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Python', 'Python Developer'),
        ('DBMS', 'Database Administrator'),
        ('Operating System', 'OS Engineer'),
        ('Computer Networks', 'Network Engineer'),
        ('DevOps', 'DevOps Engineer'),
        ('SQL', 'SQL Developer'),
        ('Machine Learning', 'Data Scientist'),
    ])
    career_goal = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('DevOps Engineer', 'DevOps Engineer'),
        ('Backend Developer', 'Backend Developer'),
        ('Data Scientist', 'Data Scientist'),
    ])
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
