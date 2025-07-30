// CareerGraph Main JavaScript

// Global variables
let selectedPath = [];
let currentUniversities = [];

// API base URL
const API_BASE = '/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    loadPopularUniversities();
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    // University search
    const searchInput = document.getElementById('universitySearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(searchUniversities, 300));
    }
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load popular universities
async function loadPopularUniversities() {
    const container = document.getElementById('popularUniversities');
    
    try {
        const response = await axios.get(`${API_BASE}/popular-universities/`);
        const universities = response.data;
        
        container.innerHTML = '';
        
        if (universities.length === 0) {
            container.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-info-circle mb-2"></i>
                    <div>No universities found. Start by adding some data!</div>
                </div>
            `;
            return;
        }
        
        universities.slice(0, 10).forEach(university => {
            const item = createUniversityItem(university);
            container.appendChild(item);
        });
        
        currentUniversities = universities;
        
    } catch (error) {
        console.error('Error loading universities:', error);
        container.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-triangle mb-2"></i>
                <div>Error loading universities</div>
            </div>
        `;
    }
}

// Create university list item
function createUniversityItem(university) {
    const item = document.createElement('div');
    item.className = 'list-group-item university-item';
    item.onclick = () => selectUniversity(university.name);
    
    item.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-1">${university.name}</h6>
            </div>
            <span class="badge bg-primary rounded-pill">${university.profiles_count}</span>
        </div>
    `;
    
    return item;
}

// Search universities
async function searchUniversities() {
    const query = document.getElementById('universitySearch').value.trim();
    const container = document.getElementById('popularUniversities');
    
    if (query.length === 0) {
        loadPopularUniversities();
        return;
    }
    
    if (query.length < 2) {
        return;
    }
    
    try {
        // Filter current universities first
        const filtered = currentUniversities.filter(uni => 
            uni.name.toLowerCase().includes(query.toLowerCase())
        );
        
        container.innerHTML = '';
        
        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-search mb-2"></i>
                    <div>No universities found matching "${query}"</div>
                </div>
            `;
        } else {
            filtered.slice(0, 10).forEach(university => {
                const item = createUniversityItem(university);
                container.appendChild(item);
            });
        }
        
    } catch (error) {
        console.error('Error searching universities:', error);
    }
}

// Select university and start path
async function selectUniversity(universityName) {
    // Clear existing path
    selectedPath = [];
    
    // Add university to path
    selectedPath.push({
        type: 'university',
        value: universityName
    });
    
    // Update UI
    updateSelectedPath();
    showPathExplorer();
    
    // Load next steps
    await loadNextSteps();
    
    // Update selected university in list
    document.querySelectorAll('.university-item').forEach(item => {
        item.classList.remove('selected');
        if (item.textContent.includes(universityName)) {
            item.classList.add('selected');
        }
    });
}

// Update selected path display
function updateSelectedPath() {
    const pathContainer = document.getElementById('selectedPath');
    const breadcrumbContainer = document.getElementById('pathBreadcrumb');
    
    if (selectedPath.length === 0) {
        pathContainer.style.display = 'none';
        return;
    }
    
    pathContainer.style.display = 'block';
    breadcrumbContainer.innerHTML = '';
    
    selectedPath.forEach((node, index) => {
        const badge = document.createElement('span');
        badge.className = `path-badge ${node.type}`;
        badge.innerHTML = `
            <i class="fas fa-${getNodeIcon(node.type)} me-1"></i>
            ${node.value}
        `;
        breadcrumbContainer.appendChild(badge);
        
        // Add arrow if not last item
        if (index < selectedPath.length - 1) {
            const arrow = document.createElement('span');
            arrow.innerHTML = '<i class="fas fa-arrow-right text-muted"></i>';
            breadcrumbContainer.appendChild(arrow);
        }
    });
}

// Get icon for node type
function getNodeIcon(type) {
    switch (type) {
        case 'university': return 'university';
        case 'company': return 'building';
        case 'title': return 'briefcase';
        default: return 'circle';
    }
}

// Show path explorer
function showPathExplorer() {
    const explorer = document.getElementById('pathExplorer');
    explorer.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="mt-2">Loading career paths...</div>
        </div>
    `;
}

// Load next steps
async function loadNextSteps() {
    const nextStepsContainer = document.getElementById('nextSteps');
    const nextStepsList = document.getElementById('nextStepsList');
    
    try {
        const response = await axios.post(`${API_BASE}/next-steps/`, {
            selected_nodes: selectedPath,
            limit: 12
        });
        
        const data = response.data;
        
        if (data.next_steps && data.next_steps.length > 0) {
            nextStepsList.innerHTML = '';
            
            data.next_steps.forEach(step => {
                const item = createNextStepItem(step);
                nextStepsList.appendChild(item);
            });
            
            nextStepsContainer.style.display = 'block';
            document.getElementById('pathExplorer').style.display = 'none';
            
        } else {
            showNoNextSteps();
        }
        
    } catch (error) {
        console.error('Error loading next steps:', error);
        showErrorMessage('Error loading career paths');
    }
}

// Create next step item
function createNextStepItem(step) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4 mb-3';
    
    const item = document.createElement('div');
    item.className = 'next-step-item';
    item.onclick = () => selectNextStep(step);
    
    item.innerHTML = `
        <h6>
            <i class="fas fa-${getNodeIcon(step.type)} me-1"></i>
            ${truncateText(step.value, 25)}
        </h6>
        <div class="d-flex justify-content-between align-items-center">
            <small class="text-muted">${step.type}</small>
            <span class="badge bg-primary">${step.profiles_count}</span>
        </div>
    `;
    
    col.appendChild(item);
    return col;
}

// Select next step
async function selectNextStep(step) {
    selectedPath.push({
        type: step.type,
        value: step.value
    });
    
    updateSelectedPath();
    await loadNextSteps();
}

// Clear path
function clearPath() {
    selectedPath = [];
    updateSelectedPath();
    
    // Reset UI
    document.getElementById('nextSteps').style.display = 'none';
    document.getElementById('pathExplorer').innerHTML = `
        <div class="text-center p-5 text-muted">
            <i class="fas fa-arrow-left fa-2x mb-3"></i>
            <h6>Select a university to start exploring career paths</h6>
            <p>Choose your starting point from the universities on the left to see possible career trajectories.</p>
        </div>
    `;
    
    // Clear profile results
    document.getElementById('profileResults').innerHTML = `
        <div class="text-center p-3 text-muted">
            <i class="fas fa-search fa-2x mb-3"></i>
            <h6>Build your path to find profiles</h6>
            <p>As you select career steps, we'll show you LinkedIn profiles of people who followed similar paths.</p>
        </div>
    `;
    
    // Remove selection from universities
    document.querySelectorAll('.university-item').forEach(item => {
        item.classList.remove('selected');
    });
}

// Find matching profiles
async function findProfiles() {
    if (selectedPath.length === 0) {
        alert('Please select at least one career step');
        return;
    }
    
    const resultsContainer = document.getElementById('profileResults');
    resultsContainer.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="mt-2">Finding profiles...</div>
        </div>
    `;
    
    try {
        const response = await axios.post(`${API_BASE}/profile-search/`, {
            selected_nodes: selectedPath,
            limit: 20
        });
        
        const data = response.data;
        
        if (data.profiles && data.profiles.length > 0) {
            resultsContainer.innerHTML = `
                <div class="mb-3">
                    <h6>Found ${data.total_matches} matching profiles</h6>
                    <small class="text-muted">Showing top ${data.profiles.length} results</small>
                </div>
                <div class="scrollable">
                    ${data.profiles.map(profile => createProfileCard(profile)).join('')}
                </div>
            `;
        } else {
            resultsContainer.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-user-times fa-2x mb-3"></i>
                    <h6>No matching profiles found</h6>
                    <p>Try adjusting your career path to find more matches.</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error finding profiles:', error);
        resultsContainer.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-triangle mb-2"></i>
                <div>Error loading profiles</div>
            </div>
        `;
    }
}

// Create profile card
function createProfileCard(profile) {
    return `
        <div class="profile-card" onclick="showProfileDetails(${profile.id})">
            <h6>${profile.full_name}</h6>
            <p class="text-muted small mb-2">${profile.headline || 'No headline'}</p>
            <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">
                    <i class="fas fa-map-marker-alt me-1"></i>
                    ${profile.location || 'Unknown'}
                </small>
                <a href="${profile.linkedin_url}" target="_blank" class="btn btn-outline-primary btn-sm" onclick="event.stopPropagation()">
                    <i class="fab fa-linkedin me-1"></i>
                    LinkedIn
                </a>
            </div>
        </div>
    `;
}

// Show profile details
async function showProfileDetails(profileId) {
    const modal = new bootstrap.Modal(document.getElementById('profileModal'));
    const content = document.getElementById('profileContent');
    
    content.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    modal.show();
    
    try {
        const response = await axios.get(`${API_BASE}/profiles/${profileId}/`);
        const profile = response.data;
        
        content.innerHTML = `
            <div class="row">
                <div class="col-md-12">
                    <h4>${profile.full_name}</h4>
                    <p class="text-muted">${profile.headline || 'No headline'}</p>
                    <p><i class="fas fa-map-marker-alt me-2"></i>${profile.location || 'Unknown location'}</p>
                    
                    ${profile.summary ? `<div class="mb-4"><h6>Summary</h6><p>${profile.summary}</p></div>` : ''}
                    
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Education</h6>
                            ${profile.educations && profile.educations.length > 0 ? 
                                profile.educations.map(edu => `
                                    <div class="mb-2">
                                        <strong>${edu.university.name}</strong><br>
                                        <small>${edu.degree ? edu.degree.name : ''} ${edu.major ? 'in ' + edu.major.name : ''}</small><br>
                                        <small class="text-muted">${edu.start_year || ''} - ${edu.end_year || ''}</small>
                                    </div>
                                `).join('') :
                                '<p class="text-muted">No education information</p>'
                            }
                        </div>
                        <div class="col-md-6">
                            <h6>Experience</h6>
                            ${profile.experiences && profile.experiences.length > 0 ?
                                profile.experiences.slice(0, 5).map(exp => `
                                    <div class="mb-2">
                                        <strong>${exp.title}</strong><br>
                                        <small>${exp.company.name}</small><br>
                                        <small class="text-muted">${exp.start_date || ''} - ${exp.is_current ? 'Present' : (exp.end_date || '')}</small>
                                    </div>
                                `).join('') :
                                '<p class="text-muted">No experience information</p>'
                            }
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-3 text-center">
                <a href="${profile.linkedin_url}" target="_blank" class="btn btn-primary">
                    <i class="fab fa-linkedin me-1"></i>
                    View on LinkedIn
                </a>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading profile details:', error);
        content.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-triangle mb-2"></i>
                <div>Error loading profile details</div>
            </div>
        `;
    }
}

// Show statistics
async function showStatistics() {
    const modal = new bootstrap.Modal(document.getElementById('statisticsModal'));
    const content = document.getElementById('statisticsContent');
    
    content.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    modal.show();
    
    try {
        const response = await axios.get(`${API_BASE}/graph/statistics/`);
        const stats = response.data;
        
        content.innerHTML = `
            <div class="row">
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-card">
                        <span class="stat-number">${stats.total_profiles.toLocaleString()}</span>
                        <div class="stat-label">LinkedIn Profiles</div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-card">
                        <span class="stat-number">${stats.total_universities.toLocaleString()}</span>
                        <div class="stat-label">Universities</div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-card">
                        <span class="stat-number">${stats.total_companies.toLocaleString()}</span>
                        <div class="stat-label">Companies</div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-card">
                        <span class="stat-number">${stats.total_connections.toLocaleString()}</span>
                        <div class="stat-label">Career Connections</div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <h6>Top Universities</h6>
                    <div class="list-group">
                        ${stats.top_universities.map(uni => `
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                ${uni.value}
                                <span class="badge bg-primary rounded-pill">${uni.profiles_count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Top Companies</h6>
                    <div class="list-group">
                        ${stats.top_companies.map(company => `
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                ${company.value}
                                <span class="badge bg-success rounded-pill">${company.profiles_count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        content.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-triangle mb-2"></i>
                <div>Error loading statistics</div>
            </div>
        `;
    }
}

// Utility functions
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

function showNoNextSteps() {
    document.getElementById('nextSteps').style.display = 'none';
    document.getElementById('pathExplorer').innerHTML = `
        <div class="text-center p-5 text-muted">
            <i class="fas fa-graduation-cap fa-2x mb-3"></i>
            <h6>End of career path</h6>
            <p>No additional career steps found for this path. Try finding matching profiles to see who followed this trajectory.</p>
        </div>
    `;
}

function showErrorMessage(message) {
    document.getElementById('pathExplorer').innerHTML = `
        <div class="text-center p-5 text-danger">
            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
            <h6>Error</h6>
            <p>${message}</p>
        </div>
    `;
}