from django.db import models
from django.contrib.auth.models import User

class CodingQuestion(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    input_format = models.TextField()
    output_format = models.TextField()
    sample_input = models.TextField()
    sample_output = models.TextField()
    difficulty = models.CharField(max_length=10, choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')])
    
    # Store test cases as JSON array: [{"input": "string", "output": "string"}]
    test_cases = models.JSONField()

    def __str__(self):
        return self.title

class CodingAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coding_attempts')
    question = models.ForeignKey(CodingQuestion, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=20, default='Python')
    status = models.CharField(max_length=30) # "Passed", "Failed", "Compilation Error", "Timeout"
    marks = models.IntegerField()
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.question.title} ({self.status})"
