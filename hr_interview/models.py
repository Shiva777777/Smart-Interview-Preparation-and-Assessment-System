from django.db import models
from django.contrib.auth.models import User

class HRQuestion(models.Model):
    text = models.TextField()
    key_phrases = models.TextField(help_text="Comma-separated keywords/phrases to look for in the candidate's answer.")
    explanation = models.TextField(help_text="Best practices/tips on how to frame the response.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.text[:50] + "..."

class HRAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hr_attempts')
    question = models.ForeignKey(HRQuestion, on_delete=models.CASCADE)
    user_answer = models.TextField()
    feedback = models.TextField()
    score = models.IntegerField() # Percentage representation of quality
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - HR QID: {self.question.id} ({self.score}%)"
