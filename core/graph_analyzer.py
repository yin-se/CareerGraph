import networkx as nx
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
from django.db.models import Q, Count
from .models import (
    LinkedInProfile, PathNode, PathConnection, University, 
    Company, Education, Experience, CareerPath
)
import logging

logger = logging.getLogger(__name__)


class CareerGraphAnalyzer:
    """
    Analyzes career paths and generates recommendations based on graph data
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._load_graph_data()
    
    def _load_graph_data(self):
        """Load career path data into NetworkX graph"""
        self.graph.clear()
        
        # Add all nodes
        for node in PathNode.objects.all():
            self.graph.add_node(
                node.id,
                type=node.type,
                value=node.value,
                profiles_count=node.profiles_count
            )
        
        # Add all connections as edges
        for connection in PathConnection.objects.all():
            self.graph.add_edge(
                connection.from_node.id,
                connection.to_node.id,
                weight=connection.weight,
                profiles=list(connection.profiles.values_list('id', flat=True))
            )
        
        logger.info(f"Loaded graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
    
    def reload_graph(self):
        """Reload graph data from database"""
        self._load_graph_data()
    
    def find_career_paths_from_university(self, university_name: str, max_depth: int = 5) -> Dict:
        """
        Find career paths starting from a specific university
        """
        try:
            # Find university node
            university_nodes = [
                node_id for node_id, data in self.graph.nodes(data=True)
                if data['type'] == 'university' and data['value'] == university_name
            ]
            
            if not university_nodes:
                return {'error': f'University "{university_name}" not found in graph'}
            
            university_node = university_nodes[0]
            paths = []
            
            # Use DFS to find paths from university
            for path in self._dfs_paths_from_node(university_node, max_depth):
                path_info = self._analyze_path(path)
                if path_info:
                    paths.append(path_info)
            
            # Sort paths by popularity (number of profiles)
            paths.sort(key=lambda x: x['total_profiles'], reverse=True)
            
            return {
                'university': university_name,
                'total_paths': len(paths),
                'paths': paths[:50]  # Limit to top 50 paths
            }
            
        except Exception as e:
            logger.error(f"Error finding career paths from {university_name}: {e}")
            return {'error': str(e)}
    
    def find_next_steps(self, selected_nodes: List[Dict]) -> Dict:
        """
        Find possible next steps given a sequence of selected nodes
        """
        try:
            if not selected_nodes:
                return {'error': 'No nodes selected'}
            
            # Find the last node in the sequence
            last_node_info = selected_nodes[-1]
            last_node_id = self._find_node_id(last_node_info['type'], last_node_info['value'])
            
            if not last_node_id:
                return {'error': f'Node not found: {last_node_info}'}
            
            # Get all outgoing connections from the last node
            next_steps = []
            
            if last_node_id in self.graph:
                for successor in self.graph.successors(last_node_id):
                    edge_data = self.graph.edges[last_node_id, successor]
                    node_data = self.graph.nodes[successor]
                    
                    # Filter profiles that match the full path
                    matching_profiles = self._filter_profiles_by_path(
                        edge_data['profiles'], selected_nodes
                    )
                    
                    if matching_profiles:
                        next_steps.append({
                            'type': node_data['type'],
                            'value': node_data['value'],
                            'profiles_count': len(matching_profiles),
                            'total_weight': edge_data['weight'],
                            'matching_profiles': matching_profiles[:10]  # Sample of profiles
                        })
            
            # Sort by number of matching profiles
            next_steps.sort(key=lambda x: x['profiles_count'], reverse=True)
            
            return {
                'current_path': selected_nodes,
                'next_steps': next_steps[:20]  # Top 20 next steps
            }
            
        except Exception as e:
            logger.error(f"Error finding next steps: {e}")
            return {'error': str(e)}
    
    def get_profiles_for_path(self, selected_nodes: List[Dict], limit: int = 50) -> Dict:
        """
        Get LinkedIn profiles that match a specific career path
        """
        try:
            if not selected_nodes:
                return {'profiles': []}
            
            # Find profiles that match all nodes in the path
            matching_profiles = self._find_profiles_matching_path(selected_nodes)
            
            # Get detailed profile information
            profiles_data = []
            profile_objects = LinkedInProfile.objects.filter(
                id__in=matching_profiles[:limit]
            ).prefetch_related('educations__university', 'experiences__company')
            
            for profile in profile_objects:
                profile_data = {
                    'id': profile.id,
                    'full_name': profile.full_name,
                    'headline': profile.headline,
                    'location': profile.location,
                    'linkedin_url': profile.linkedin_url,
                    'education': [],
                    'experience': []
                }
                
                # Add education data
                for edu in profile.educations.all()[:3]:  # Limit to 3 most recent
                    profile_data['education'].append({
                        'university': edu.university.name,
                        'degree': edu.degree.name if edu.degree else '',
                        'major': edu.major.name if edu.major else '',
                        'years': f"{edu.start_year or ''}-{edu.end_year or ''}"
                    })
                
                # Add experience data
                for exp in profile.experiences.all()[:5]:  # Limit to 5 most recent
                    profile_data['experience'].append({
                        'title': exp.title,
                        'company': exp.company.name,
                        'duration': f"{exp.start_date or ''} - {exp.end_date or 'Present' if exp.is_current else ''}",
                        'is_current': exp.is_current
                    })
                
                profiles_data.append(profile_data)
            
            return {
                'path': selected_nodes,
                'total_matches': len(matching_profiles),
                'profiles': profiles_data
            }
            
        except Exception as e:
            logger.error(f"Error getting profiles for path: {e}")
            return {'error': str(e)}
    
    def get_popular_universities(self, limit: int = 50) -> List[Dict]:
        """Get most popular universities by number of alumni in database"""
        try:
            universities = PathNode.objects.filter(
                type='university'
            ).order_by('-profiles_count')[:limit]
            
            return [
                {
                    'name': uni.value,
                    'profiles_count': uni.profiles_count,
                    'id': uni.id
                }
                for uni in universities
            ]
            
        except Exception as e:
            logger.error(f"Error getting popular universities: {e}")
            return []
    
    def get_career_statistics(self, university_name: str) -> Dict:
        """Get career statistics for a university"""
        try:
            # Find profiles from this university
            university_profiles = LinkedInProfile.objects.filter(
                educations__university__name=university_name
            ).distinct()
            
            if not university_profiles.exists():
                return {'error': f'No profiles found for {university_name}'}
            
            # Analyze career paths
            companies = Counter()
            titles = Counter()
            industries = Counter()
            
            for profile in university_profiles:
                for exp in profile.experiences.all():
                    companies[exp.company.name] += 1
                    titles[exp.title] += 1
                    if exp.company.industry:
                        industries[exp.company.industry] += 1
            
            return {
                'university': university_name,
                'total_profiles': university_profiles.count(),
                'top_companies': dict(companies.most_common(20)),
                'top_titles': dict(titles.most_common(20)),
                'top_industries': dict(industries.most_common(10))
            }
            
        except Exception as e:
            logger.error(f"Error getting career statistics: {e}")
            return {'error': str(e)}
    
    def _dfs_paths_from_node(self, start_node: int, max_depth: int) -> List[List[int]]:
        """Find all paths from a starting node using DFS"""
        paths = []
        
        def dfs(current_node, path, depth):
            if depth >= max_depth:
                return
            
            if len(path) > 1:  # At least start node + one more
                paths.append(path.copy())
            
            for successor in self.graph.successors(current_node):
                if successor not in path:  # Avoid cycles
                    path.append(successor)
                    dfs(successor, path, depth + 1)
                    path.pop()
        
        dfs(start_node, [start_node], 0)
        return paths
    
    def _analyze_path(self, path: List[int]) -> Optional[Dict]:
        """Analyze a path and extract meaningful information"""
        try:
            if len(path) < 2:
                return None
            
            path_nodes = []
            total_profiles = 0
            min_weight = float('inf')
            
            # Analyze each step in the path
            for i in range(len(path) - 1):
                from_node = path[i]
                to_node = path[i + 1]
                
                if not self.graph.has_edge(from_node, to_node):
                    return None
                
                edge_data = self.graph.edges[from_node, to_node]
                from_data = self.graph.nodes[from_node]
                to_data = self.graph.nodes[to_node]
                
                path_nodes.append({
                    'from': {
                        'type': from_data['type'],
                        'value': from_data['value']
                    },
                    'to': {
                        'type': to_data['type'],
                        'value': to_data['value']
                    },
                    'weight': edge_data['weight'],
                    'profiles_count': len(edge_data['profiles'])
                })
                
                min_weight = min(min_weight, edge_data['weight'])
            
            # The path strength is the minimum connection weight
            total_profiles = min_weight
            
            return {
                'steps': path_nodes,
                'total_profiles': total_profiles,
                'path_length': len(path),
                'strength_score': self._calculate_path_strength(path)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing path: {e}")
            return None
    
    def _calculate_path_strength(self, path: List[int]) -> float:
        """Calculate a strength score for a career path"""
        if len(path) < 2:
            return 0.0
        
        total_weight = 0
        total_connections = 0
        
        for i in range(len(path) - 1):
            if self.graph.has_edge(path[i], path[i + 1]):
                weight = self.graph.edges[path[i], path[i + 1]]['weight']
                total_weight += weight
                total_connections += 1
        
        if total_connections == 0:
            return 0.0
        
        # Average weight per connection, normalized by path length
        return (total_weight / total_connections) / len(path)
    
    def _find_node_id(self, node_type: str, node_value: str) -> Optional[int]:
        """Find node ID by type and value"""
        for node_id, data in self.graph.nodes(data=True):
            if data['type'] == node_type and data['value'] == node_value:
                return node_id
        return None
    
    def _filter_profiles_by_path(self, profile_ids: List[int], selected_nodes: List[Dict]) -> List[int]:
        """Filter profiles that match the complete selected path"""
        if not selected_nodes:
            return profile_ids
        
        # This is a simplified implementation
        # In production, you'd want more sophisticated path matching
        matching_profiles = []
        
        for profile_id in profile_ids:
            try:
                profile = LinkedInProfile.objects.get(id=profile_id)
                if self._profile_matches_path(profile, selected_nodes):
                    matching_profiles.append(profile_id)
            except LinkedInProfile.DoesNotExist:
                continue
        
        return matching_profiles
    
    def _profile_matches_path(self, profile: LinkedInProfile, selected_nodes: List[Dict]) -> bool:
        """Check if a profile matches a given path"""
        # Extract profile's career sequence
        profile_sequence = []
        
        # Add universities
        for edu in profile.educations.all().order_by('end_year'):
            profile_sequence.append({
                'type': 'university',
                'value': edu.university.name
            })
        
        # Add companies/titles
        for exp in profile.experiences.all().order_by('start_date'):
            profile_sequence.append({
                'type': 'company',
                'value': exp.company.name
            })
            profile_sequence.append({
                'type': 'title',
                'value': exp.title
            })
        
        # Check if selected nodes appear in the profile sequence in order
        selected_index = 0
        for seq_item in profile_sequence:
            if selected_index < len(selected_nodes):
                selected_node = selected_nodes[selected_index]
                if (seq_item['type'] == selected_node['type'] and 
                    seq_item['value'] == selected_node['value']):
                    selected_index += 1
        
        return selected_index == len(selected_nodes)
    
    def _find_profiles_matching_path(self, selected_nodes: List[Dict]) -> List[int]:
        """Find all profiles that match a specific career path"""
        if not selected_nodes:
            return []
        
        # Start with all profiles
        matching_profiles = set(LinkedInProfile.objects.values_list('id', flat=True))
        
        for node in selected_nodes:
            node_profiles = set()
            
            if node['type'] == 'university':
                node_profiles = set(
                    LinkedInProfile.objects.filter(
                        educations__university__name=node['value']
                    ).values_list('id', flat=True)
                )
            elif node['type'] == 'company':
                node_profiles = set(
                    LinkedInProfile.objects.filter(
                        experiences__company__name=node['value']
                    ).values_list('id', flat=True)
                )
            elif node['type'] == 'title':
                node_profiles = set(
                    LinkedInProfile.objects.filter(
                        experiences__title=node['value']
                    ).values_list('id', flat=True)
                )
            
            # Intersect with previous results
            matching_profiles = matching_profiles.intersection(node_profiles)
        
        return list(matching_profiles)


class CareerPathRecommender:
    """
    Provides career path recommendations based on graph analysis
    """
    
    def __init__(self):
        self.analyzer = CareerGraphAnalyzer()
    
    def recommend_next_steps(self, user_profile: Dict, num_recommendations: int = 10) -> List[Dict]:
        """
        Recommend next career steps based on user's current profile
        """
        try:
            current_path = self._extract_user_path(user_profile)
            recommendations = self.analyzer.find_next_steps(current_path)
            
            if 'next_steps' in recommendations:
                return recommendations['next_steps'][:num_recommendations]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def find_similar_profiles(self, user_profile: Dict, limit: int = 20) -> List[Dict]:
        """
        Find profiles with similar career paths
        """
        try:
            current_path = self._extract_user_path(user_profile)
            result = self.analyzer.get_profiles_for_path(current_path, limit)
            
            if 'profiles' in result:
                return result['profiles']
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error finding similar profiles: {e}")
            return []
    
    def _extract_user_path(self, user_profile: Dict) -> List[Dict]:
        """Extract career path from user profile"""
        path = []
        
        # Add education
        if 'education' in user_profile:
            for edu in user_profile['education']:
                if 'university' in edu:
                    path.append({
                        'type': 'university',
                        'value': edu['university']
                    })
        
        # Add experience
        if 'experience' in user_profile:
            for exp in user_profile['experience']:
                if 'company' in exp:
                    path.append({
                        'type': 'company',
                        'value': exp['company']
                    })
                if 'title' in exp:
                    path.append({
                        'type': 'title',
                        'value': exp['title']
                    })
        
        return path