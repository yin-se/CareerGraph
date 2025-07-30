from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
import uuid

from .models import (
    University, Company, LinkedInProfile, PathNode, 
    PathConnection, UserQuery
)
from .serializers import (
    UniversitySerializer, CompanySerializer, LinkedInProfileSerializer,
    LinkedInProfileBasicSerializer, PathNodeSerializer, PathConnectionSerializer,
    CareerPathQuerySerializer, NextStepsQuerySerializer, ProfileSearchSerializer,
    UniversityStatsSerializer, CareerPathResponseSerializer,
    NextStepsResponseSerializer, ProfileSearchResponseSerializer,
    UniversityStatsResponseSerializer, PopularUniversitiesSerializer,
    UserQuerySerializer
)
from .graph_analyzer import CareerGraphAnalyzer, CareerPathRecommender


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def index(request):
    """Main page view"""
    return render(request, 'core/index.html')


class UniversityListView(generics.ListAPIView):
    """List all universities"""
    queryset = University.objects.all().order_by('name')
    serializer_class = UniversitySerializer
    pagination_class = StandardResultsSetPagination


class CompanyListView(generics.ListAPIView):
    """List all companies"""
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    pagination_class = StandardResultsSetPagination


class LinkedInProfileListView(generics.ListAPIView):
    """List LinkedIn profiles with filtering"""
    queryset = LinkedInProfile.objects.all().order_by('-scraped_at')
    serializer_class = LinkedInProfileBasicSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(headline__icontains=search) |
                Q(location__icontains=search)
            )
        
        # Filter by university
        university = self.request.query_params.get('university', None)
        if university:
            queryset = queryset.filter(
                educations__university__name__icontains=university
            ).distinct()
        
        # Filter by company
        company = self.request.query_params.get('company', None)
        if company:
            queryset = queryset.filter(
                experiences__company__name__icontains=company
            ).distinct()
        
        return queryset


class LinkedInProfileDetailView(generics.RetrieveAPIView):
    """Get detailed LinkedIn profile"""
    queryset = LinkedInProfile.objects.all()
    serializer_class = LinkedInProfileSerializer


class PopularUniversitiesView(APIView):
    """Get most popular universities by profile count"""
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 50))
        
        try:
            analyzer = CareerGraphAnalyzer()
            universities = analyzer.get_popular_universities(limit)
            
            serializer = PopularUniversitiesSerializer(universities, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CareerPathsFromUniversityView(APIView):
    """Get career paths starting from a specific university"""
    
    def post(self, request):
        serializer = CareerPathQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        university_name = serializer.validated_data.get('university')
        max_depth = serializer.validated_data.get('max_depth', 5)
        
        if not university_name:
            return Response(
                {'error': 'University name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            analyzer = CareerGraphAnalyzer()
            result = analyzer.find_career_paths_from_university(university_name, max_depth)
            
            if 'error' in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NextStepsView(APIView):
    """Get possible next steps given a sequence of selected nodes"""
    
    def post(self, request):
        serializer = NextStepsQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        selected_nodes = serializer.validated_data['selected_nodes']
        limit = serializer.validated_data.get('limit', 20)
        
        # Validate selected_nodes format
        for node in selected_nodes:
            if 'type' not in node or 'value' not in node:
                return Response(
                    {'error': 'Each node must have type and value fields'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            analyzer = CareerGraphAnalyzer()
            result = analyzer.find_next_steps(selected_nodes)
            
            if 'error' in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            # Limit results
            if 'next_steps' in result:
                result['next_steps'] = result['next_steps'][:limit]
            
            # Save user query for analytics
            session_id = request.session.get('session_id')
            if not session_id:
                session_id = str(uuid.uuid4())
                request.session['session_id'] = session_id
            
            UserQuery.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                selected_nodes=selected_nodes,
                results_count=len(result.get('next_steps', []))
            )
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProfileSearchView(APIView):
    """Get LinkedIn profiles that match a specific career path"""
    
    def post(self, request):
        serializer = ProfileSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        selected_nodes = serializer.validated_data['selected_nodes']
        limit = serializer.validated_data.get('limit', 50)
        
        # Validate selected_nodes format
        for node in selected_nodes:
            if 'type' not in node or 'value' not in node:
                return Response(
                    {'error': 'Each node must have type and value fields'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            analyzer = CareerGraphAnalyzer()
            result = analyzer.get_profiles_for_path(selected_nodes, limit)
            
            if 'error' in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UniversityStatisticsView(APIView):
    """Get career statistics for a university"""
    
    def post(self, request):
        serializer = UniversityStatsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        university_name = serializer.validated_data['university_name']
        
        try:
            analyzer = CareerGraphAnalyzer()
            result = analyzer.get_career_statistics(university_name)
            
            if 'error' in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecommendationsView(APIView):
    """Get career path recommendations based on user profile"""
    
    def post(self, request):
        user_profile = request.data.get('user_profile', {})
        num_recommendations = int(request.data.get('num_recommendations', 10))
        
        try:
            recommender = CareerPathRecommender()
            recommendations = recommender.recommend_next_steps(user_profile, num_recommendations)
            
            return Response({
                'recommendations': recommendations,
                'count': len(recommendations)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimilarProfilesView(APIView):
    """Find profiles with similar career paths"""
    
    def post(self, request):
        user_profile = request.data.get('user_profile', {})
        limit = int(request.data.get('limit', 20))
        
        try:
            recommender = CareerPathRecommender()
            similar_profiles = recommender.find_similar_profiles(user_profile, limit)
            
            return Response({
                'similar_profiles': similar_profiles,
                'count': len(similar_profiles)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PathNodesView(generics.ListAPIView):
    """List path nodes with filtering"""
    queryset = PathNode.objects.all().order_by('-profiles_count')
    serializer_class = PathNodeSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by node type
        node_type = self.request.query_params.get('type', None)
        if node_type:
            queryset = queryset.filter(type=node_type)
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(value__icontains=search)
        
        # Filter by minimum profile count
        min_profiles = self.request.query_params.get('min_profiles', None)
        if min_profiles:
            try:
                min_count = int(min_profiles)
                queryset = queryset.filter(profiles_count__gte=min_count)
            except ValueError:
                pass
        
        return queryset


class PathConnectionsView(generics.ListAPIView):
    """List path connections"""
    queryset = PathConnection.objects.all().order_by('-weight')
    serializer_class = PathConnectionSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by from_node type
        from_type = self.request.query_params.get('from_type', None)
        if from_type:
            queryset = queryset.filter(from_node__type=from_type)
        
        # Filter by to_node type
        to_type = self.request.query_params.get('to_type', None)
        if to_type:
            queryset = queryset.filter(to_node__type=to_type)
        
        # Filter by minimum weight
        min_weight = self.request.query_params.get('min_weight', None)
        if min_weight:
            try:
                min_w = int(min_weight)
                queryset = queryset.filter(weight__gte=min_w)
            except ValueError:
                pass
        
        return queryset


@api_view(['GET'])
def graph_statistics(request):
    """Get overall graph statistics"""
    try:
        stats = {
            'total_profiles': LinkedInProfile.objects.count(),
            'total_universities': University.objects.count(),
            'total_companies': Company.objects.count(),
            'total_nodes': PathNode.objects.count(),
            'total_connections': PathConnection.objects.count(),
            'node_types': {
                'university': PathNode.objects.filter(type='university').count(),
                'company': PathNode.objects.filter(type='company').count(),
                'title': PathNode.objects.filter(type='title').count(),
            },
            'top_universities': list(
                PathNode.objects.filter(type='university')
                .order_by('-profiles_count')[:10]
                .values('value', 'profiles_count')
            ),
            'top_companies': list(
                PathNode.objects.filter(type='company')
                .order_by('-profiles_count')[:10]
                .values('value', 'profiles_count')
            ),
        }
        
        return Response(stats)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def reload_graph(request):
    """Reload the career graph from database"""
    try:
        analyzer = CareerGraphAnalyzer()
        analyzer.reload_graph()
        
        return Response({
            'message': 'Graph reloaded successfully',
            'nodes': analyzer.graph.number_of_nodes(),
            'edges': analyzer.graph.number_of_edges()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
