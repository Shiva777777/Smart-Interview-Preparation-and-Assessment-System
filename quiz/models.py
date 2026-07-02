from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    DOMAIN_CHOICES = [
        ('Python', 'Python'),
        ('DBMS', 'DBMS'),
        ('Operating System', 'Operating System'),
        ('Computer Networks', 'Computer Networks'),
        ('DevOps', 'DevOps'),
        ('SQL', 'SQL'),
        ('Machine Learning', 'Machine Learning'),
    ]

    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    domain = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField()
    
    # AI Follow-up system integration
    follow_up_question = models.TextField(blank=True, null=True)
    follow_up_explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.domain} | {self.difficulty}] {self.text[:50]}..."

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    domain = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=10)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    
    # Cheat detection variables
    tab_switches = models.IntegerField(default=0)
    window_minimizes = models.IntegerField(default=0)
    focus_lost = models.IntegerField(default=0)
    
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.domain} ({self.completed_at.strftime('%Y-%m-%d')})"

class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, blank=True, null=True)
    is_correct = models.BooleanField()

    def __str__(self):
        return f"{self.attempt.user.username} - QID: {self.question.id} - Correct: {self.is_correct}"
