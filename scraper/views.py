from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import render
from .models import ScrapingJob, ScrapingTarget
from .tasks import scrape_linkedin_profiles
from .serializers import ScrapingJobSerializer, CreateScrapingJobSerializer


class ScrapingJobListView(generics.ListAPIView):
    """List scraping jobs (admin only)"""
    queryset = ScrapingJob.objects.all().order_by('-created_at')
    serializer_class = ScrapingJobSerializer
    permission_classes = [IsAdminUser]


class ScrapingJobDetailView(generics.RetrieveAPIView):
    """Get scraping job details (admin only)"""
    queryset = ScrapingJob.objects.all()
    serializer_class = ScrapingJobSerializer
    permission_classes = [IsAdminUser]


class CreateScrapingJobView(APIView):
    """Create a new scraping job (admin only)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = CreateScrapingJobSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the job
        job = ScrapingJob.objects.create(
            name=serializer.validated_data['name'],
            search_query=serializer.validated_data.get('search_query', ''),
            created_by=request.user
        )
        
        # Create targets
        targets_data = serializer.validated_data.get('targets', [])
        for target_data in targets_data:
            ScrapingTarget.objects.create(
                job=job,
                type=target_data['type'],
                query=target_data['query'],
                max_profiles=target_data.get('max_profiles', 50)
            )
        
        # Return created job
        response_serializer = ScrapingJobSerializer(job)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class StartScrapingJobView(APIView):
    """Start a scraping job (admin only)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        try:
            job = ScrapingJob.objects.get(pk=pk)
            
            if job.status != 'pending':
                return Response(
                    {'error': 'Job can only be started if it is pending'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Start the scraping job
            scrape_linkedin_profiles.delay(job.id)
            
            job.status = 'running'
            job.save()
            
            serializer = ScrapingJobSerializer(job)
            return Response(serializer.data)
            
        except ScrapingJob.DoesNotExist:
            return Response(
                {'error': 'Job not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
