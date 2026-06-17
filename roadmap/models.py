from django.db import models
from django.contrib.auth.models import User

class RoadmapProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='roadmap_progress')
    goal = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.goal} Roadmap"

class Milestone(models.Model):
    roadmap = models.ForeignKey(RoadmapProgress, on_delete=models.CASCADE, related_name='milestones')
    month = models.IntegerField()
    topic = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Month {self.month} - {self.topic} ({'Completed' if self.completed else 'Pending'})"
