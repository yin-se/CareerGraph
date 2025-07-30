from rest_framework import serializers
from .models import ScrapingJob, ScrapingTarget, ScrapingResult, ScrapingError


class ScrapingTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingTarget
        fields = ['id', 'type', 'query', 'max_profiles', 'scraped_count']


class ScrapingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingResult
        fields = ['id', 'linkedin_url', 'linkedin_id', 'scraped_at', 'processing_status']


class ScrapingErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingError
        fields = ['id', 'url', 'error_type', 'error_message', 'occurred_at']


class ScrapingJobSerializer(serializers.ModelSerializer):
    targets = ScrapingTargetSerializer(many=True, read_only=True)
    results = ScrapingResultSerializer(many=True, read_only=True)
    errors = ScrapingErrorSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ScrapingJob
        fields = [
            'id', 'name', 'status', 'started_at', 'completed_at',
            'profiles_scraped', 'profiles_failed', 'error_message',
            'search_query', 'created_by_username', 'created_at',
            'targets', 'results', 'errors'
        ]


class CreateScrapingJobSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    search_query = serializers.CharField(required=False, allow_blank=True)
    targets = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        allow_empty=False
    )
    
    def validate_targets(self, value):
        """Validate targets format"""
        for target in value:
            if 'type' not in target or 'query' not in target:
                raise serializers.ValidationError(
                    "Each target must have 'type' and 'query' fields"
                )
            
            valid_types = ['university', 'company', 'keyword', 'profile_url']
            if target['type'] not in valid_types:
                raise serializers.ValidationError(
                    f"Target type must be one of: {valid_types}"
                )
        
        return value