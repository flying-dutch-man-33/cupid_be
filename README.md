# Quick start (local development)

Follow these steps to run the project locally.

## Prerequisites
- Python 3.8+ installed
- Poetry installed (dependency and virtual environment manager)

Install Poetry (recommended):
```bash
# via official installer
curl -sSL https://install.python-poetry.org | python3 -
# or via pipx
pipx install poetry
```

Confirm Poetry is available:
```bash
poetry --version
```

## Setup and run

1. Install project dependencies:
```bash
poetry install
```

2. Activate the Poetry virtual environment (optional — you can also prefix commands with `poetry run`):
```bash
poetry shell
```
If you prefer not to spawn a shell, use:
```bash
poetry run <command>
# e.g. poetry run python manage.py runserver
```

3. (Optional) Apply database migrations:
```bash
poetry run python manage.py migrate
```

4. Start the development server:
```bash
poetry run python manage.py runserver
# or, if you used `poetry shell`, just:
# python manage.py runserver
```

The app will be available at http://127.0.0.1:8000 by default.

## Notes
- Use `poetry run` to execute commands inside the project's virtual environment without activating it manually.
- If you need a specific Python version, point Poetry to it before installing: `poetry env use /path/to/python`.