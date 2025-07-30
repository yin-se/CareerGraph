# CareerGraph

A Django web application that analyzes LinkedIn career paths to help users explore career trajectories based on educational backgrounds and professional experiences.

## Features

- **Ethical LinkedIn Data Scraping**: Respects robots.txt and rate limits
- **Career Path Analysis**: Graph-based analysis of career progressions
- **Interactive Frontend**: Explore career paths starting from universities
- **RESTful API**: Comprehensive API for career data queries
- **Scheduled Data Collection**: Weekly automated scraping
- **Graph Visualization**: NetworkX-powered career path analysis

## Architecture

### Backend
- **Django 4.2**: Web framework
- **PostgreSQL**: Database for structured data storage
- **Celery**: Asynchronous task processing
- **Redis**: Message broker and caching
- **NetworkX**: Graph analysis and algorithms
- **Django REST Framework**: API development

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **D3.js**: Data visualization
- **Axios**: HTTP client for API calls
- **Vanilla JavaScript**: Interactive functionality

### Key Models
- **LinkedInProfile**: User profile data
- **University/Company**: Educational and professional entities
- **Education/Experience**: Career history
- **PathNode/PathConnection**: Graph representation
- **CareerPath**: Serialized career trajectories

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js (for frontend assets)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CareerGraph
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis configurations
   ```

5. **Setup database**
   ```bash
   # Create PostgreSQL database
   createdb careergraph
   
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Setup scheduled tasks**
   ```bash
   python manage.py setup_weekly_scraping
   ```

## Usage

### Running the Application

1. **Start Redis server**
   ```bash
   redis-server
   ```

2. **Start Celery worker**
   ```bash
   celery -A careergraph worker --loglevel=info
   ```

3. **Start Celery beat scheduler**
   ```bash
   celery -A careergraph beat --loglevel=info
   ```

4. **Start Django development server**
   ```bash
   python manage.py runserver
   ```

5. **Access the application**
   - Main interface: http://localhost:8000
   - Admin interface: http://localhost:8000/admin
   - API documentation: http://localhost:8000/api

### Manual Data Collection

Run a manual scraping job:
```bash
python manage.py run_scraping_job --university "Stanford University" --max-profiles 50
```

### API Endpoints

#### Career Path Analysis
- `GET /api/popular-universities/` - Get popular universities
- `POST /api/career-paths/` - Get career paths from university
- `POST /api/next-steps/` - Get next career steps
- `POST /api/profile-search/` - Find matching profiles

#### Data Management
- `GET /api/universities/` - List universities
- `GET /api/companies/` - List companies
- `GET /api/profiles/` - List LinkedIn profiles
- `GET /api/nodes/` - List career path nodes
- `GET /api/connections/` - List career connections

#### Statistics
- `GET /api/graph/statistics/` - Overall graph statistics
- `POST /api/university-stats/` - University-specific statistics

## API Usage Examples

### Find Career Paths from University
```javascript
const response = await axios.post('/api/career-paths/', {
    university: 'Stanford University',
    max_depth: 5
});
```

### Get Next Career Steps
```javascript
const response = await axios.post('/api/next-steps/', {
    selected_nodes: [
        { type: 'university', value: 'Stanford University' },
        { type: 'company', value: 'Google' }
    ],
    limit: 20
});
```

### Search for Matching Profiles
```javascript
const response = await axios.post('/api/profile-search/', {
    selected_nodes: [
        { type: 'university', value: 'MIT' },
        { type: 'title', value: 'Software Engineer' }
    ],
    limit: 50
});
```

## Data Model

### Core Entities
```python
# University and educational data
University -> Education -> LinkedInProfile
Major -> Education
Degree -> Education

# Professional experience
Company -> Experience -> LinkedInProfile

# Career path representation
LinkedInProfile -> CareerPath
PathNode -> PathConnection
```

### Graph Structure
- **Nodes**: Universities, Companies, Job Titles
- **Edges**: Career transitions with weights
- **Profiles**: Associated with nodes and connections

## Ethical Considerations

This application follows ethical data collection practices:

- **Public Data Only**: Only scrapes publicly accessible LinkedIn information
- **Rate Limiting**: Respects server resources with conservative limits
- **Robots.txt Compliance**: Checks and follows robots.txt directives
- **Educational Purpose**: Designed for career research and guidance
- **Data Retention**: Configurable data retention policies
- **Privacy Focused**: No private or sensitive information collection

## Development

### Adding New Features

1. **Backend API**: Add views in `core/views.py`
2. **Frontend**: Update templates and JavaScript in `core/static/`
3. **Data Models**: Modify `core/models.py` and create migrations
4. **Scraping**: Extend `scraper/linkedin_scraper.py`

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Format code
black .

# Check code quality
flake8 .

# Type checking
mypy .
```

## Deployment

### Production Settings
1. Set `DEBUG=False` in environment
2. Configure secure database credentials  
3. Setup proper Redis configuration
4. Use production WSGI server (gunicorn)
5. Configure reverse proxy (nginx)
6. Setup SSL certificates
7. Configure monitoring and logging

### Environment Variables
```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
DATABASE_NAME=careergraph_prod
DATABASE_USER=careergraph_user
DATABASE_PASSWORD=secure-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is for educational and research purposes. Please respect LinkedIn's terms of service and ethical data collection practices.

## Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

## Roadmap

- [ ] Machine learning career predictions
- [ ] Advanced data visualizations
- [ ] Mobile-responsive improvements
- [ ] Integration with other professional networks
- [ ] Advanced filtering and search
- [ ] User account management
- [ ] Career recommendations engine
- [ ] Export to various formats