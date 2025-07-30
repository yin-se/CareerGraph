from rest_framework import serializers
from .models import (
    University, Company, Major, Degree, LinkedInProfile,
    Education, Experience, CareerPath, PathNode, PathConnection, UserQuery
)


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'country', 'city', 'website']


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'industry', 'size', 'website', 'linkedin_url']


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = ['id', 'name', 'field']


class DegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree
        fields = ['id', 'name', 'type']


class EducationSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    degree = DegreeSerializer(read_only=True)
    major = MajorSerializer(read_only=True)
    
    class Meta:
        model = Education
        fields = [
            'id', 'university', 'degree', 'major', 
            'start_year', 'end_year', 'gpa', 'activities', 'description'
        ]


class ExperienceSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = Experience
        fields = [
            'id', 'company', 'title', 'employment_type', 'location',
            'start_date', 'end_date', 'is_current', 'description'
        ]


class LinkedInProfileSerializer(serializers.ModelSerializer):
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    
    class Meta:
        model = LinkedInProfile
        fields = [
            'id', 'linkedin_id', 'linkedin_url', 'full_name', 'headline',
            'location', 'summary', 'profile_image_url', 'is_premium',
            'educations', 'experiences', 'scraped_at', 'created_at'
        ]


class LinkedInProfileBasicSerializer(serializers.ModelSerializer):
    """Simplified serializer for profile lists"""
    class Meta:
        model = LinkedInProfile
        fields = [
            'id', 'linkedin_id', 'linkedin_url', 'full_name', 
            'headline', 'location'
        ]


class PathNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathNode
        fields = ['id', 'type', 'value', 'profiles_count', 'created_at']


class PathConnectionSerializer(serializers.ModelSerializer):
    from_node = PathNodeSerializer(read_only=True)
    to_node = PathNodeSerializer(read_only=True)
    
    class Meta:
        model = PathConnection
        fields = ['id', 'from_node', 'to_node', 'weight']


class CareerPathQuerySerializer(serializers.Serializer):
    """Serializer for career path query requests"""
    university = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    max_depth = serializers.IntegerField(default=5, min_value=1, max_value=10)
    limit = serializers.IntegerField(default=50, min_value=1, max_value=200)


class NextStepsQuerySerializer(serializers.Serializer):
    """Serializer for next steps query requests"""
    selected_nodes = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        allow_empty=False
    )
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)


class ProfileSearchSerializer(serializers.Serializer):
    """Serializer for profile search requests"""
    selected_nodes = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        allow_empty=False
    )
    limit = serializers.IntegerField(default=50, min_value=1, max_value=200)


class UniversityStatsSerializer(serializers.Serializer):
    """Serializer for university statistics"""
    university_name = serializers.CharField(required=True)


class CareerPathResponseSerializer(serializers.Serializer):
    """Serializer for career path response"""
    university = serializers.CharField()
    total_paths = serializers.IntegerField()
    paths = serializers.ListField(child=serializers.DictField())


class NextStepsResponseSerializer(serializers.Serializer):
    """Serializer for next steps response"""
    current_path = serializers.ListField(child=serializers.DictField())
    next_steps = serializers.ListField(child=serializers.DictField())


class ProfileSearchResponseSerializer(serializers.Serializer):
    """Serializer for profile search response"""
    path = serializers.ListField(child=serializers.DictField())
    total_matches = serializers.IntegerField()
    profiles = serializers.ListField(child=serializers.DictField())


class UniversityStatsResponseSerializer(serializers.Serializer):
    """Serializer for university statistics response"""
    university = serializers.CharField()
    total_profiles = serializers.IntegerField()
    top_companies = serializers.DictField()
    top_titles = serializers.DictField()
    top_industries = serializers.DictField()


class PopularUniversitiesSerializer(serializers.Serializer):
    """Serializer for popular universities list"""
    name = serializers.CharField()
    profiles_count = serializers.IntegerField()
    id = serializers.IntegerField()


class UserQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuery
        fields = ['id', 'selected_nodes', 'results_count', 'created_at']
        read_only_fields = ['id', 'created_at']