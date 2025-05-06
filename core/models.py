from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Customuser(AbstractUser):
    """Custom User model for the SmartExam application"""
    dob = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    college = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    mob = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return self.username


class ExamHistory(models.Model):
    """Model to track exam predictions made by users"""
    user = models.ForeignKey(Customuser, on_delete=models.CASCADE, related_name='exam_history')
    subject = models.CharField(max_length=200)
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    question_count = models.IntegerField(default=5)
    difficulty = models.CharField(max_length=20, default='medium', 
                            choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
    specific_topics = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Exam Histories"
    
    def __str__(self):
        return f"{self.subject} - {self.user.username}"


class SavedQuestion(models.Model):
    """Model to store questions saved by users for later review"""
    user = models.ForeignKey(Customuser, on_delete=models.CASCADE, related_name='saved_questions')
    exam_history = models.ForeignKey(ExamHistory, on_delete=models.CASCADE, related_name='saved_questions')
    question_text = models.TextField()
    answer_text = models.TextField()
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Saved question for {self.user.username} - {self.question_text[:50]}..."


class Session(models.Model):
    """Model to track user sessions and activity"""
    user = models.ForeignKey(Customuser, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Session for {self.user.username if self.user else 'Anonymous'}"


