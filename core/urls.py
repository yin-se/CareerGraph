from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'core'

urlpatterns = [
    # Main page
    path('', views.index, name='index'),
    
    # API endpoints
    path('api/universities/', views.UniversityListView.as_view(), name='university-list'),
    path('api/companies/', views.CompanyListView.as_view(), name='company-list'),
    
    # Profile endpoints
    path('api/profiles/', views.LinkedInProfileListView.as_view(), name='profile-list'),
    path('api/profiles/<int:pk>/', views.LinkedInProfileDetailView.as_view(), name='profile-detail'),
    
    # Career path analysis endpoints
    path('api/popular-universities/', views.PopularUniversitiesView.as_view(), name='popular-universities'),
    path('api/career-paths/', views.CareerPathsFromUniversityView.as_view(), name='career-paths'),
    path('api/next-steps/', views.NextStepsView.as_view(), name='next-steps'),
    path('api/profile-search/', views.ProfileSearchView.as_view(), name='profile-search'),
    path('api/university-stats/', views.UniversityStatisticsView.as_view(), name='university-stats'),
    
    # Recommendation endpoints
    path('api/recommendations/', views.RecommendationsView.as_view(), name='recommendations'),
    path('api/similar-profiles/', views.SimilarProfilesView.as_view(), name='similar-profiles'),
    
    # Graph data endpoints
    path('api/nodes/', views.PathNodesView.as_view(), name='path-nodes'),
    path('api/connections/', views.PathConnectionsView.as_view(), name='path-connections'),
    path('api/graph/statistics/', views.graph_statistics, name='graph-statistics'),
    path('api/graph/reload/', views.reload_graph, name='reload-graph'),
]