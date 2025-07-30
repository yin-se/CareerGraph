// Career Explorer specific functionality

// Advanced career path exploration functions
class CareerExplorer {
    constructor() {
        this.currentPath = [];
        this.pathHistory = [];
        this.recommendations = [];
    }

    // Initialize the explorer
    init() {
        this.setupAdvancedFeatures();
        this.loadRecommendations();
    }

    // Setup advanced features
    setupAdvancedFeatures() {
        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearCurrentPath();
            } else if (e.ctrlKey && e.key === 'z') {
                this.undoLastStep();
            }
        });

        // Add path comparison feature
        this.setupPathComparison();
    }

    // Setup path comparison
    setupPathComparison() {
        const compareBtn = document.createElement('button');
        compareBtn.className = 'btn btn-outline-info btn-sm';
        compareBtn.innerHTML = '<i class="fas fa-balance-scale me-1"></i>Compare Paths';
        compareBtn.onclick = () => this.openPathComparison();

        // Add to the UI if path is selected
        if (selectedPath.length > 1) {
            const pathContainer = document.getElementById('selectedPath');
            if (pathContainer) {
                pathContainer.appendChild(compareBtn);
            }
        }
    }

    // Open path comparison modal
    async openPathComparison() {
        // Create and show comparison modal
        const modalHtml = `
            <div class="modal fade" id="pathComparisonModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Career Path Comparison</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div id="pathComparisonContent">
                                <div class="text-center p-3">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to DOM if it doesn't exist
        if (!document.getElementById('pathComparisonModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }

        const modal = new bootstrap.Modal(document.getElementById('pathComparisonModal'));
        modal.show();

        // Load comparison data
        await this.loadPathComparison();
    }

    // Load path comparison data
    async loadPathComparison() {
        const content = document.getElementById('pathComparisonContent');
        
        try {
            // Get similar paths
            const response = await axios.post('/api/similar-paths/', {
                selected_nodes: selectedPath,
                limit: 5
            });

            const similarPaths = response.data.similar_paths || [];

            content.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Your Selected Path</h6>
                        <div class="path-visualization">
                            ${this.renderPathVisualization(selectedPath, 'primary')}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>Similar Career Paths</h6>
                        <div class="similar-paths">
                            ${similarPaths.map(path => 
                                this.renderPathVisualization(path.nodes, 'secondary')
                            ).join('')}
                        </div>
                    </div>
                </div>
            `;

        } catch (error) {
            console.error('Error loading path comparison:', error);
            content.innerHTML = `
                <div class="text-center p-3 text-danger">
                    <i class="fas fa-exclamation-triangle mb-2"></i>
                    <div>Error loading path comparison</div>
                </div>
            `;
        }
    }

    // Render path visualization
    renderPathVisualization(path, colorScheme = 'primary') {
        return `
            <div class="path-flow">
                ${path.map((node, index) => `
                    <div class="path-node ${colorScheme}">
                        <i class="fas fa-${getNodeIcon(node.type)} me-1"></i>
                        ${node.value}
                    </div>
                    ${index < path.length - 1 ? '<div class="path-arrow"><i class="fas fa-arrow-down"></i></div>' : ''}
                `).join('')}
            </div>
        `;
    }

    // Load personalized recommendations
    async loadRecommendations() {
        if (selectedPath.length === 0) return;

        try {
            const response = await axios.post('/api/recommendations/', {
                user_profile: this.buildUserProfile(),
                num_recommendations: 5
            });

            this.recommendations = response.data.recommendations || [];
            this.displayRecommendations();

        } catch (error) {
            console.error('Error loading recommendations:', error);
        }
    }

    // Build user profile from selected path
    buildUserProfile() {
        const profile = {
            education: [],
            experience: []
        };

        selectedPath.forEach(node => {
            if (node.type === 'university') {
                profile.education.push({ university: node.value });
            } else if (node.type === 'company') {
                profile.experience.push({ company: node.value });
            } else if (node.type === 'title') {
                if (profile.experience.length > 0) {
                    profile.experience[profile.experience.length - 1].title = node.value;
                } else {
                    profile.experience.push({ title: node.value });
                }
            }
        });

        return profile;
    }

    // Display recommendations
    displayRecommendations() {
        if (this.recommendations.length === 0) return;

        const recommendationsHtml = `
            <div class="recommendations-section mt-3">
                <h6 class="text-success">
                    <i class="fas fa-magic me-1"></i>
                    Personalized Recommendations
                </h6>
                <div class="recommendations-list">
                    ${this.recommendations.map(rec => `
                        <div class="recommendation-item" onclick="selectNextStep(${JSON.stringify(rec).replace(/"/g, '&quot;')})">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${rec.value}</strong>
                                    <small class="text-muted d-block">${rec.type}</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-success">${rec.profiles_count}</span>
                                    <div><small class="text-muted">${Math.round(rec.confidence || 0)}% match</small></div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        const nextStepsContainer = document.getElementById('nextSteps');
        if (nextStepsContainer) {
            nextStepsContainer.insertAdjacentHTML('beforeend', recommendationsHtml);
        }
    }

    // Undo last step
    undoLastStep() {
        if (selectedPath.length > 1) {
            this.pathHistory.push([...selectedPath]);
            selectedPath.pop();
            updateSelectedPath();
            loadNextSteps();
        }
    }

    // Clear current path
    clearCurrentPath() {
        if (selectedPath.length > 0) {
            this.pathHistory.push([...selectedPath]);
            clearPath();
        }
    }

    // Export path data
    exportPath() {
        const pathData = {
            path: selectedPath,
            timestamp: new Date().toISOString(),
            recommendations: this.recommendations
        };

        const blob = new Blob([JSON.stringify(pathData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `career-path-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Import path data
    importPath(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const pathData = JSON.parse(e.target.result);
                selectedPath = pathData.path || [];
                updateSelectedPath();
                loadNextSteps();
            } catch (error) {
                alert('Error importing path data');
            }
        };
        reader.readAsText(file);
    }
}

// Advanced search functionality
class AdvancedSearch {
    constructor() {
        this.searchHistory = [];
        this.savedSearches = [];
    }

    // Advanced university search with filters
    async searchUniversitiesAdvanced(query, filters = {}) {
        try {
            const params = new URLSearchParams();
            params.append('search', query);
            
            if (filters.country) params.append('country', filters.country);
            if (filters.minProfiles) params.append('min_profiles', filters.minProfiles);

            const response = await axios.get(`/api/universities/?${params}`);
            return response.data.results || [];

        } catch (error) {
            console.error('Error in advanced search:', error);
            return [];
        }
    }

    // Search profiles with advanced filters
    async searchProfilesAdvanced(filters) {
        try {
            const response = await axios.post('/api/profiles/search/', filters);
            return response.data;

        } catch (error) {
            console.error('Error in advanced profile search:', error);
            return { profiles: [], total_matches: 0 };
        }
    }

    // Save search for later
    saveSearch(searchData) {
        const savedSearch = {
            id: Date.now(),
            name: searchData.name || `Search ${this.savedSearches.length + 1}`,
            filters: searchData.filters,
            timestamp: new Date().toISOString()
        };

        this.savedSearches.push(savedSearch);
        localStorage.setItem('careerGraphSavedSearches', JSON.stringify(this.savedSearches));
    }

    // Load saved searches
    loadSavedSearches() {
        const saved = localStorage.getItem('careerGraphSavedSearches');
        if (saved) {
            this.savedSearches = JSON.parse(saved);
        }
    }
}

// Data visualization utilities
class DataVisualization {
    constructor() {
        this.colors = {
            university: '#0dcaf0',
            company: '#198754',
            title: '#ffc107'
        };
    }

    // Create career path flow chart
    createPathFlowChart(containerId, pathData) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const svg = container.append("svg")
            .attr("width", "100%")
            .attr("height", 400);

        const width = container.node().getBoundingClientRect().width;
        const height = 400;

        // Create nodes and links
        const nodes = pathData.map((node, i) => ({
            id: i,
            type: node.type,
            value: node.value,
            x: (width / (pathData.length + 1)) * (i + 1),
            y: height / 2
        }));

        const links = [];
        for (let i = 0; i < nodes.length - 1; i++) {
            links.push({
                source: i,
                target: i + 1
            });
        }

        // Draw links
        svg.selectAll(".link")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .attr("x1", d => nodes[d.source].x)
            .attr("y1", d => nodes[d.source].y)
            .attr("x2", d => nodes[d.target].x)
            .attr("y2", d => nodes[d.target].y)
            .attr("stroke", "#6c757d")
            .attr("stroke-width", 2)
            .attr("marker-end", "url(#arrowhead)");

        // Add arrowhead marker
        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 8)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#6c757d");

        // Draw nodes
        const nodeGroups = svg.selectAll(".node")
            .data(nodes)
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.x},${d.y})`);

        nodeGroups.append("circle")
            .attr("r", 30)
            .attr("fill", d => this.colors[d.type] || "#6c757d")
            .attr("stroke", "#fff")
            .attr("stroke-width", 3);

        nodeGroups.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .attr("fill", "#fff")
            .attr("font-size", "12px")
            .attr("font-weight", "bold")
            .text(d => this.truncateText(d.value, 10));

        // Add labels below nodes
        nodeGroups.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "50")
            .attr("font-size", "12px")
            .attr("fill", "#6c757d")
            .text(d => d.type);
    }

    // Create statistics chart
    createStatsChart(containerId, statsData) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = { top: 20, right: 30, bottom: 40, left: 40 };
        const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;

        const svg = container.append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const g = svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // Create scales
        const x = d3.scaleBand()
            .rangeRound([0, width])
            .padding(0.1)
            .domain(statsData.map(d => d.label));

        const y = d3.scaleLinear()
            .rangeRound([height, 0])
            .domain([0, d3.max(statsData, d => d.value)]);

        // Add axes
        g.append("g")
            .attr("class", "axis axis--x")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x));

        g.append("g")
            .attr("class", "axis axis--y")
            .call(d3.axisLeft(y));

        // Add bars
        g.selectAll(".bar")
            .data(statsData)
            .enter().append("rect")
            .attr("class", "bar")
            .attr("x", d => x(d.label))
            .attr("y", d => y(d.value))
            .attr("width", x.bandwidth())
            .attr("height", d => height - y(d.value))
            .attr("fill", "#0d6efd");
    }

    // Utility function to truncate text
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }
}

// Initialize advanced features
document.addEventListener('DOMContentLoaded', function() {
    window.careerExplorer = new CareerExplorer();
    window.advancedSearch = new AdvancedSearch();
    window.dataVisualization = new DataVisualization();

    // Initialize advanced features
    careerExplorer.init();
    advancedSearch.loadSavedSearches();

    // Add export/import functionality
    addAdvancedControls();
});

// Add advanced controls to the UI
function addAdvancedControls() {
    const pathContainer = document.getElementById('selectedPath');
    if (pathContainer) {
        const controlsHtml = `
            <div class="advanced-controls mt-2">
                <button class="btn btn-outline-secondary btn-sm me-1" onclick="careerExplorer.exportPath()">
                    <i class="fas fa-download me-1"></i>Export
                </button>
                <input type="file" id="importFile" accept=".json" style="display: none;" onchange="handleFileImport(event)">
                <button class="btn btn-outline-secondary btn-sm me-1" onclick="document.getElementById('importFile').click()">
                    <i class="fas fa-upload me-1"></i>Import
                </button>
                <button class="btn btn-outline-info btn-sm" onclick="showAdvancedFilters()">
                    <i class="fas fa-filter me-1"></i>Filters
                </button>
            </div>
        `;
        
        pathContainer.insertAdjacentHTML('beforeend', controlsHtml);
    }
}

// Handle file import
function handleFileImport(event) {
    const file = event.target.files[0];
    if (file) {
        careerExplorer.importPath(file);
    }
}

// Show advanced filters modal
function showAdvancedFilters() {
    // Implementation for advanced filters modal
    console.log('Advanced filters modal - to be implemented');
}