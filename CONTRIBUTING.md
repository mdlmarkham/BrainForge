# Contributing to BrainForge

Thank you for your interest in contributing to BrainForge! This document provides guidelines and instructions for contributing to the project.

## 🎯 Code of Conduct

By participating in this project, you are expected to uphold our code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Welcome diverse perspectives
- Be patient with newcomers

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Basic understanding of FastAPI and Pydantic

### Development Setup

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/brainforge.git
   cd brainforge
   ```

3. **Set up development environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```

## 📝 Development Workflow

### Branch Naming Convention
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation improvements
- `refactor/description` - Code refactoring

### Commit Message Guidelines
Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following coding standards
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass**
6. **Submit a pull request** with clear description

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

### Test Guidelines
- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies appropriately

## 🎨 Code Style

### Python Standards
- Follow PEP 8 guidelines
- Use type hints throughout
- Document public functions with docstrings
- Keep functions small and focused
- Use meaningful variable names

### Pydantic Models
- Use Pydantic v2.12.5 syntax
- Include descriptive field descriptions
- Implement proper validation
- Follow constitutional compliance requirements

### Linting and Formatting
```bash
# Check code quality
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/
```

## 🏛️ Constitutional Compliance

All contributions must adhere to BrainForge's constitutional principles:

### Required for AI-Generated Content
- Track AI generation with `AIGeneratedMixin`
- Include AI justification when applicable
- Implement human review workflows

### Data Provenance
- Use `ProvenanceMixin` for all entities
- Track creation source and modifications
- Maintain audit trails

### Version Control
- Implement `VersionMixin` for version tracking
- Maintain complete change history
- Support rollback capabilities

## 📚 Documentation

### Code Documentation
- Document all public functions and classes
- Include type hints in function signatures
- Use Google-style docstrings

### API Documentation
- Keep OpenAPI specifications updated
- Include example requests and responses
- Document authentication requirements

### User Documentation
- Update README.md for significant changes
- Add usage examples for new features
- Document configuration options

## 🐛 Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Error messages or logs

## 💡 Feature Requests

For feature requests, please:
- Describe the problem you're solving
- Explain the proposed solution
- Provide use cases or examples
- Consider backward compatibility

## 🔧 Code Review Process

### Review Checklist
- [ ] Code follows project standards
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Constitutional compliance is maintained
- [ ] No security vulnerabilities introduced
- [ ] Performance considerations addressed

### Review Guidelines
- Be constructive and specific
- Focus on code quality, not personal style
- Suggest improvements with examples
- Acknowledge good practices

## 🚨 Security Issues

For security vulnerabilities, please:
- **Do not** open a public issue
- Email security@example.com with details
- Include steps to reproduce
- Provide suggested fixes if possible

## 📞 Getting Help

- Check existing documentation first
- Search existing issues and discussions
- Ask questions in GitHub Discussions
- Join our community chat (if available)

## 🙏 Acknowledgments

We appreciate all contributions, no matter how small! Every bug report, feature suggestion, or documentation improvement helps make BrainForge better.

Thank you for contributing! 🎉