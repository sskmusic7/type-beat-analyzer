# Contributing to Type Beat Analyzer

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/type-beat-analyzer.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit: `git commit -m "Add your feature"`
6. Push: `git push origin feature/your-feature-name`
7. Open a Pull Request

## Development Setup

Follow the setup instructions in [QUICKSTART.md](QUICKSTART.md) to get your development environment running.

## Code Style

### Python
- Follow PEP 8 style guide
- Use type hints where possible
- Format with `black`
- Lint with `flake8`

### TypeScript/React
- Follow Next.js conventions
- Use TypeScript for all new files
- Format with Prettier (if configured)

## Areas for Contribution

### High Priority
- [ ] Improve model accuracy with better data augmentation
- [ ] Add more artists to the training dataset
- [ ] Optimize inference speed
- [ ] Add unit tests
- [ ] Improve error handling

### Features
- [ ] Batch upload support
- [ ] Export analysis reports
- [ ] Mobile app (React Native)
- [ ] Real-time audio analysis
- [ ] Integration with BeatStars/Airbit APIs

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Architecture diagrams
- [ ] Video tutorials
- [ ] Blog posts about the tech stack

## Testing

Before submitting a PR, please:
1. Test your changes locally
2. Ensure the backend API works
3. Test the frontend UI
4. Run any existing tests

## Questions?

Open an issue with the `question` label or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
