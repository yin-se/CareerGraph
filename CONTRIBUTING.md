# Contributing to CareerGraph

Thank you for your interest in contributing to CareerGraph! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/CareerGraph.git
   cd CareerGraph
   ```
3. **Set up the development environment** following the README.md instructions
4. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

## 📋 How to Contribute

### 🐛 Bug Reports
- Use the GitHub issue tracker
- Include detailed reproduction steps
- Provide system information (OS, Python version, etc.)
- Include error messages and logs

### ✨ Feature Requests
- Check existing issues first
- Provide clear use cases
- Explain the expected behavior
- Consider implementation complexity

### 💻 Code Contributions

1. **Follow Python/Django best practices**
2. **Write tests** for new functionality
3. **Update documentation** as needed
4. **Follow the existing code style**
5. **Keep commits atomic and well-described**

### 🧪 Running Tests
```bash
python manage.py test
```

### 📝 Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Comment complex logic

## 🎯 Priority Areas for Contribution

- **Frontend improvements** (UI/UX enhancements)
- **Data visualization** (new chart types, interactive features)
- **API enhancements** (new endpoints, better filtering)
- **Performance optimizations** (database queries, caching)
- **Testing** (unit tests, integration tests)
- **Documentation** (API docs, tutorials)
- **Accessibility** (WCAG compliance, keyboard navigation)

## 🔄 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update the README.md** if needed
5. **Submit the pull request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots if UI changes

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [NetworkX Documentation](https://networkx.org/)
- [Bootstrap Documentation](https://getbootstrap.com/)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Maintain a positive environment

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: Contact the maintainers for sensitive issues

## 🏷️ Labels

We use these labels for issues and PRs:
- `bug`: Something isn't working
- `enhancement`: New feature or request
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `documentation`: Improvements to docs
- `frontend`: Frontend-related changes
- `backend`: Backend-related changes

Thank you for contributing to CareerGraph! 🚀