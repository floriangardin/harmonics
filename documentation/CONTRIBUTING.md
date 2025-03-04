# Contributing to Harmonics

Thank you for considering contributing to Harmonics! This document outlines the process for contributing to the language and related tools.

## Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/harmonics.git
   cd harmonics
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install the package in development mode
   ```

4. **Install Development Tools**
   ```bash
   pip install pytest pytest-cov black flake8
   ```

## Coding Guidelines

### Python Code Style

Harmonics follows PEP 8 with a few specific guidelines:

- Use 4 spaces for indentation
- Maximum line length of 100 characters
- Use docstrings for all public methods, functions, and classes
- Use type hints where appropriate
- Use descriptive variable names

We use Black for code formatting:

```bash
# Format all Python files
black .

# Check formatting without changing files
black --check .
```

### Language Grammar

When modifying the Harmonics language grammar:

1. Document all changes in comments
2. Update the language specification in `documentation/LANGUAGE_SYNTAX.md`
3. Add appropriate test cases in `tests/grammar/`
4. Update the parser accordingly

## Testing

All contributions should include tests:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=harmonics

# Run a specific test file
pytest tests/test_parser.py
```

For language changes:
- Add syntax examples to `tests/examples/`
- Add unit tests for parser components in `tests/parser/`
- Add integration tests showing complete examples in `tests/integration/`

## Documentation

Documentation is as important as code:

1. **Update User Documentation**
   - Add examples for new features
   - Update syntax documentation
   - Ensure README examples work

2. **Update Developer Documentation**
   - Document design decisions
   - Update API documentation

3. **In-Code Documentation**
   - Add comments explaining complex logic
   - Use descriptive variable names
   - Include docstrings

## Issue Reporting

When reporting issues:

1. Use the issue template
2. Include a minimal reproducible example
3. Specify your environment (OS, Python version, etc.)
4. For language issues, include a sample piece that demonstrates the problem

## Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the coding guidelines
   - Add tests
   - Update documentation

3. **Run Tests Locally**
   ```bash
   pytest
   black --check .
   flake8
   ```

4. **Commit Your Changes**
   - Use meaningful commit messages
   - Reference issue numbers if applicable

5. **Submit a Pull Request**
   - Describe the changes in detail
   - Explain how to test the changes
   - Link related issues

6. **Code Review**
   - Address review comments
   - Update your PR as needed

## Language Evolution Process

For changes to the Harmonics language itself:

1. **Proposal Stage**
   - Create an issue with the [Language Proposal] prefix
   - Include syntax examples and use cases
   - Discuss with the community

2. **Draft Implementation**
   - Create a proof of concept
   - Document trade-offs and design decisions

3. **Review and Refinement**
   - Get feedback on the implementation
   - Make adjustments based on feedback

4. **Final Implementation**
   - Complete implementation with tests
   - Update documentation
   - Submit PR for final review

## Versioning

Harmonics follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible language changes
- **MINOR** version for new features in a backward-compatible manner
- **PATCH** version for backward-compatible bug fixes

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Acknowledge contributions from others

## License

By contributing to Harmonics, you agree that your contributions will be licensed under the project's MIT License.
