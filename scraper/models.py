from django.db import models
from django.contrib.auth.models import User


class ScrapingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    profiles_scraped = models.PositiveIntegerField(default=0)
    profiles_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    search_query = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']


class ScrapingTarget(models.Model):
    TARGET_TYPES = [
        ('university', 'University Alumni'),
        ('company', 'Company Employees'),
        ('keyword', 'Keyword Search'),
        ('profile_url', 'Direct Profile URL'),
    ]
    
    job = models.ForeignKey(ScrapingJob, on_delete=models.CASCADE, related_name='targets')
    type = models.CharField(max_length=20, choices=TARGET_TYPES)
    query = models.CharField(max_length=500)
    max_profiles = models.PositiveIntegerField(default=100)
    scraped_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.query}"


class ScrapingResult(models.Model):
    job = models.ForeignKey(ScrapingJob, on_delete=models.CASCADE, related_name='results')
    target = models.ForeignKey(ScrapingTarget, on_delete=models.CASCADE, related_name='results')
    linkedin_url = models.URLField()
    linkedin_id = models.CharField(max_length=100, blank=True)
    profile_data = models.JSONField(default=dict)
    scraped_at = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(max_length=20, default='raw')
    
    def __str__(self):
        return f"Result for {self.linkedin_url}"
    
    class Meta:
        unique_together = ['job', 'linkedin_url']


class ScrapingError(models.Model):
    job = models.ForeignKey(ScrapingJob, on_delete=models.CASCADE, related_name='errors')
    target = models.ForeignKey(ScrapingTarget, on_delete=models.CASCADE, related_name='errors', null=True, blank=True)
    url = models.URLField(blank=True)
    error_type = models.CharField(max_length=100)
    error_message = models.TextField()
    occurred_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.error_type}: {self.url}"
    
    class Meta:
        ordering = ['-occurred_at']
