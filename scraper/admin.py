from django.contrib import admin
from .models import ScrapingJob, ScrapingTarget, ScrapingResult, ScrapingError


class ScrapingTargetInline(admin.TabularInline):
    model = ScrapingTarget
    extra = 0


class ScrapingResultInline(admin.TabularInline):
    model = ScrapingResult
    extra = 0
    readonly_fields = ['scraped_at', 'processing_status']


class ScrapingErrorInline(admin.TabularInline):
    model = ScrapingError
    extra = 0
    readonly_fields = ['occurred_at']


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'profiles_scraped', 'profiles_failed', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at', 'completed_at', 'created_at']
    search_fields = ['name', 'search_query']
    readonly_fields = ['started_at', 'completed_at', 'created_at']
    inlines = [ScrapingTargetInline, ScrapingResultInline, ScrapingErrorInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'status', 'search_query', 'created_by')
        }),
        ('Progress', {
            'fields': ('profiles_scraped', 'profiles_failed', 'error_message')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'created_at')
        }),
    )


@admin.register(ScrapingTarget)
class ScrapingTargetAdmin(admin.ModelAdmin):
    list_display = ['job', 'type', 'query', 'max_profiles', 'scraped_count']
    list_filter = ['type', 'job__status']
    search_fields = ['query', 'job__name']


@admin.register(ScrapingResult)
class ScrapingResultAdmin(admin.ModelAdmin):
    list_display = ['job', 'linkedin_url', 'linkedin_id', 'processing_status', 'scraped_at']
    list_filter = ['processing_status', 'scraped_at', 'job__status']
    search_fields = ['linkedin_url', 'linkedin_id', 'job__name']
    readonly_fields = ['scraped_at']


@admin.register(ScrapingError)
class ScrapingErrorAdmin(admin.ModelAdmin):
    list_display = ['job', 'error_type', 'url', 'occurred_at']
    list_filter = ['error_type', 'occurred_at']
    search_fields = ['url', 'error_message', 'job__name']
    readonly_fields = ['occurred_at']
