from django.db import models
from django.contrib.auth.models import User


class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Universities"


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    industry = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Companies"


class Major(models.Model):
    name = models.CharField(max_length=200, unique=True)
    field = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name


class Degree(models.Model):
    DEGREE_TYPES = [
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
        ('mba', 'MBA'),
        ('certificate', 'Certificate'),
        ('diploma', 'Diploma'),
    ]
    
    type = models.CharField(max_length=20, choices=DEGREE_TYPES)
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class LinkedInProfile(models.Model):
    linkedin_id = models.CharField(max_length=100, unique=True)
    linkedin_url = models.URLField()
    full_name = models.CharField(max_length=200)
    headline = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)
    profile_image_url = models.URLField(blank=True)
    is_premium = models.BooleanField(default=False)
    scraped_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.linkedin_id})"


class Education(models.Model):
    profile = models.ForeignKey(LinkedInProfile, on_delete=models.CASCADE, related_name='educations')
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True, blank=True)
    major = models.ForeignKey(Major, on_delete=models.CASCADE, null=True, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    activities = models.TextField(blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.profile.full_name} - {self.university.name}"
    
    class Meta:
        ordering = ['-end_year', '-start_year']


class Experience(models.Model):
    profile = models.ForeignKey(LinkedInProfile, on_delete=models.CASCADE, related_name='experiences')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.profile.full_name} - {self.title} at {self.company.name}"
    
    class Meta:
        ordering = ['-start_date']


class CareerPath(models.Model):
    profile = models.OneToOneField(LinkedInProfile, on_delete=models.CASCADE)
    path_hash = models.CharField(max_length=64, unique=True)
    university_sequence = models.JSONField(default=list)
    company_sequence = models.JSONField(default=list)
    title_sequence = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Career path for {self.profile.full_name}"


class PathNode(models.Model):
    NODE_TYPES = [
        ('university', 'University'),
        ('company', 'Company'),
        ('title', 'Job Title'),
    ]
    
    type = models.CharField(max_length=20, choices=NODE_TYPES)
    value = models.CharField(max_length=200)
    profiles_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"
    
    class Meta:
        unique_together = ['type', 'value']


class PathConnection(models.Model):
    from_node = models.ForeignKey(PathNode, on_delete=models.CASCADE, related_name='outgoing_connections')
    to_node = models.ForeignKey(PathNode, on_delete=models.CASCADE, related_name='incoming_connections')
    weight = models.PositiveIntegerField(default=1)
    profiles = models.ManyToManyField(LinkedInProfile, blank=True)
    
    def __str__(self):
        return f"{self.from_node.value} -> {self.to_node.value} ({self.weight})"
    
    class Meta:
        unique_together = ['from_node', 'to_node']


class UserQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100)
    selected_nodes = models.JSONField(default=list)
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Query {self.id} - {len(self.selected_nodes)} nodes"
