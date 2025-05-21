# Contributing to DockerDiscordControl

Thank you for your interest in DockerDiscordControl! This document provides guidelines for contributing to the project.

## Ways to Contribute

There are various ways you can contribute to the project:

- Code contributions (features, bugfixes)
- Documentation improvements
- Testing and bug reports
- Feature suggestions and ideas
- Translations

## Setting Up Development Environment

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DockerDiscordControl.git
   cd DockerDiscordControl
   ```

2. **Set up Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Local development**:
   ```bash
   # Set environment variables
   export FLASK_APP=app
   export FLASK_ENV=development
   export FLASK_SECRET_KEY=dev_secret_key
   
   # Start Flask development server
   flask run --host=0.0.0.0 --port=8374
   
   # In another terminal, start the bot
   python bot.py
   ```

## Pull Request Process

1. **Create a feature branch**: Create a branch for your changes:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Commit your changes**: Commit your changes with meaningful commit messages:
   ```bash
   git commit -am "Feature added: Brief description"
   ```

3. **Run tests**: Ensure your changes are tested and don't break existing tests:
   ```bash
   pytest
   ```

4. **Create a Pull Request**: Push your branch and create a pull request with a clear description of your changes.

## Code Guidelines

- Follow the existing code style of the project
- Document new features with docstrings
- Write tests for new features
- Keep code simple and readable
- Use descriptive variable and function names

## Commit Messages

Use clear, descriptive commit messages in the format:

```
Category: Brief summary (max 50 chars)

Longer explanation if needed. Wrap at around 72 characters.
Explain the problem this commit solves and how it solves it.
```

Categories can be: `Feature`, `Fix`, `Docs`, `Style`, `Refactor`, `Test`, `Chore`

## License

By contributing, you agree that your changes will be released under the same MIT license as the project.

## Questions?

If you have any questions, don't hesitate to open an issue or contact the project team directly.

## Acknowledgements

We would like to express our sincere gratitude to the following individuals for their valuable contributions, support, and feedback:

- Luigi
- Flo
- Siggi
- Sedat
- Simon
- Moritz

Their dedication and input have been instrumental in making this project what it is today.

## Supporting the Project

If you find DockerDiscordControl helpful, consider supporting its development through one of the following ways:

- **Buy Me A Coffee**: [Buy Me A Coffee](https://buymeacoffee.com/dockerdiscordcontrol)
- **PayPal**: [Donate via PayPal](https://www.paypal.com/donate/?hosted_button_id=XKVC6SFXU2GW4)
- **Spread the word**: Star the repository and share it with others who might find it useful