from django.contrib import admin
from .models import (
    University, Company, Major, Degree, LinkedInProfile, 
    Education, Experience, CareerPath, PathNode, PathConnection, UserQuery
)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'city', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['name', 'city', 'country']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'size', 'created_at']
    list_filter = ['industry', 'size', 'created_at']
    search_fields = ['name', 'industry']


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ['name', 'field']
    list_filter = ['field']
    search_fields = ['name', 'field']


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']
    list_filter = ['type']
    search_fields = ['name']


@admin.register(LinkedInProfile)
class LinkedInProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'linkedin_id', 'location', 'is_premium', 'scraped_at']
    list_filter = ['is_premium', 'scraped_at', 'created_at']
    search_fields = ['full_name', 'linkedin_id', 'headline']
    readonly_fields = ['scraped_at', 'created_at']


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['profile', 'university', 'degree', 'major', 'start_year', 'end_year']
    list_filter = ['university', 'degree__type', 'start_year', 'end_year']
    search_fields = ['profile__full_name', 'university__name', 'major__name']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['profile', 'company', 'title', 'start_date', 'end_date', 'is_current']
    list_filter = ['company', 'is_current', 'start_date']
    search_fields = ['profile__full_name', 'company__name', 'title']


@admin.register(CareerPath)
class CareerPathAdmin(admin.ModelAdmin):
    list_display = ['profile', 'path_hash', 'created_at', 'updated_at']
    search_fields = ['profile__full_name', 'path_hash']
    readonly_fields = ['path_hash']


@admin.register(PathNode)
class PathNodeAdmin(admin.ModelAdmin):
    list_display = ['type', 'value', 'profiles_count', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['value']


@admin.register(PathConnection)
class PathConnectionAdmin(admin.ModelAdmin):
    list_display = ['from_node', 'to_node', 'weight']
    list_filter = ['from_node__type', 'to_node__type']
    search_fields = ['from_node__value', 'to_node__value']


@admin.register(UserQuery)
class UserQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'results_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_id']
