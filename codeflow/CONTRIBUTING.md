# Contributing to Elders Guild CodeFlow

Thank you for your interest in contributing to Elders Guild CodeFlow! This document provides guidelines for contributing to the project.

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## How to Contribute

### Reporting Issues

- Check if the issue has already been reported
- Use a clear and descriptive title
- Include steps to reproduce the issue
- Provide your environment details (VS Code version, OS, etc.)
- Include relevant logs or error messages

### Suggesting Enhancements

- Check if the enhancement has already been suggested
- Use a clear and descriptive title
- Provide a step-by-step description of the suggested enhancement
- Explain why this enhancement would be useful
- List any alternatives you've considered

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Add or update tests as needed
5. Ensure all tests pass (`npm test`)
6. Ensure code follows linting rules (`npm run lint`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

### Prerequisites

- Node.js 16.x or higher
- VS Code 1.74.0 or higher
- Git

### Setup Steps

1. Clone the repository
   ```bash
   git clone https://github.com/aicompany/codeflow.git
   cd codeflow
   ```

2. Install dependencies
   ```bash
   npm install
   ```

3. Compile TypeScript
   ```bash
   npm run compile
   ```

4. Run tests
   ```bash
   npm test
   ```

5. Open in VS Code
   ```bash
   code .
   ```

6. Press F5 to run the extension in a new VS Code window

## Coding Standards

### TypeScript

- Use TypeScript for all source code
- Enable strict mode
- Provide type annotations for all function parameters and return types
- Use interfaces for object types
- Avoid `any` type unless absolutely necessary

### Code Style

- Follow the ESLint configuration
- Use 4 spaces for indentation
- Use single quotes for strings
- Always use semicolons
- Use meaningful variable and function names
- Add JSDoc comments for public APIs

### File Organization

```
src/
├── extension.ts          # Extension entry point
├── aiCommandSystem.ts    # AI system integration
├── commandProvider.ts    # Command tree provider
├── statusProvider.ts     # Status tree provider
├── historyProvider.ts    # History provider
└── statusBar.ts          # Status bar manager
```

### Testing

- Write tests for all new features
- Follow the existing test patterns
- Ensure tests are independent and can run in any order
- Mock external dependencies appropriately
- Aim for high test coverage

## Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Examples

```
Add natural language command processing

- Implement AI-powered command discovery
- Add confidence scoring for suggestions
- Include user feedback mechanism

Fixes #123
```

## Release Process

1. Update version in `package.json`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create a tag: `git tag v1.0.0`
5. Push changes and tags: `git push origin main --tags`
6. GitHub Actions will automatically create a release

## Documentation

- Update README.md for user-facing changes
- Update inline code comments for implementation details
- Add JSDoc comments for public APIs
- Update CHANGELOG.md for all changes

## Questions?

Feel free to open an issue for any questions about contributing. We're here to help!

## License

By contributing to Elders Guild CodeFlow, you agree that your contributions will be licensed under the MIT License.
