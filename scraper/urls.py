from django.urls import path
from . import views

app_name = 'scraper'

urlpatterns = [
    # Scraping job management (for admin use)
    path('api/jobs/', views.ScrapingJobListView.as_view(), name='job-list'),
    path('api/jobs/<int:pk>/', views.ScrapingJobDetailView.as_view(), name='job-detail'),
    path('api/jobs/create/', views.CreateScrapingJobView.as_view(), name='create-job'),
    path('api/jobs/<int:pk>/start/', views.StartScrapingJobView.as_view(), name='start-job'),
]