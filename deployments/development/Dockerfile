FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIPENV_NOSPIN=1

WORKDIR /usr/src/app

# Packages required to compile mysqlclient
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Pipenv
RUN python -m pip install --upgrade pip \
    && python -m pip install pipenv

# Copy the Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install all packages (including development packages) system-wide
RUN pipenv install --dev --system

# Copy app
COPY . .

ENV DJANGO_SETTINGS_MODULE=chat_connect.settings.settings_development

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
