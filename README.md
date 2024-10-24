[python-download]: https://www.python.org/downloads/
[docker-download]: https://www.docker.com/get-started/
[mysql-download]: https://www.mysql.com/downloads/
[redis-download]: https://redis.io/download/

![Workflow branch master](https://github.com/amssdias/chatea-conecta/actions/workflows/django-ci.yml/badge.svg?branch=master)

![Python Badge](https://img.shields.io/badge/Python-3.9-blue?logo=python)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)
[![Docker](https://badgen.net/badge/icon/docker?icon=docker&label)](https://https://docker.com/)

<h1 align=center>Chatea Conecta 🌍💬</h1>

**Chatea Conecta** is a chat application that allows users to connect and chat with people from around the world.

## 🛠️ Getting started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### 🔧 Pre requisites

To run this project, you need the following tools installed:

- 🐳 [Docker][docker-download]: Required to run all services (Redis, MySQL, Django, Celery) using docker-compose.

Alternatively, you can manually install and manage the services below if not using Docker.
If not using Docker, make sure to install:

- 🐍 [Python 3.9][python-download]: Required if you plan to run the Django app directly without Docker.
- 🐬 [MySQL][mysql-download]: Required if running the database outside of Docker.
- 🛠️ [Redis][redis-download]: Required if running Redis outside of Docker.


### 🏗️ Installation


1. Clone this repository to your local machine

Open your terminal and run the following commands:


```shell
git clone https://github.com/amssdias/chatea-conecta.git
cd chatea-conecta
```
   
2. Set up environment variables:

Create a `.env` file in the project directory to configure environment variables like your Redis password, MySQL credentials, and Django settings. For example:

```shell
SECRET_KEY=<secret-key>
MYSQL_USER=<mysql-username>
MYSQL_PASSWORD=<mysql-password>
MYSQL_ROOT_PASSWORD=<mysql-root-password>
REDIS_PROTOCOL=<redis-protocol>
REDIS_PASSWORD=<redis-password>
DJANGO_REDIS_CACHE_DB=<redis-cache-db-index>
REDIS_DB_CHANNEL=<redis-channel-db-index>
REDIS_DB_CELERY=<redis-celery-db-index>
ENVIRON=<development/production>
```

3. Add redis.conf file (with same password in the `.env` file):

```bash
requirepass <your-redis-password>
```

4. 🚀 Run the application with Docker Compose:

```shell
docker-compose up --build
```

The application will be accessible at http://localhost:8000.



## Dockerfile Setup


### Dockerfile Breakdown

Below is the Dockerfile with explanations for each instruction.

```dockerfile
# Use the official Python 3.9 image from the Docker Hub
FROM python:3.9

# Set the working directory inside the container to /usr/src/app
WORKDIR /usr/src/app

RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install all packages (including development packages) system-wide
RUN pipenv install --dev --system

# Copy the rest of the application code to the working directory
COPY . .

# Expose port 8000 to the host
EXPOSE 8000

# Command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=chat_connect.settings.settings_development"]
```

### Explanation
1. Install pipenv: Install pipenv using ```pip install pipenv```.
2. Copy Pipfile and Pipfile.lock: Copy Pipfile and Pipfile.lock to the Docker container.
3. Install All Packages System-wide:
  - Use ```pipenv install --dev --system --deploy``` to install all packages, including development packages, system-wide (without creating a virtual environment).
  - The ```--system``` flag tells pipenv to install the packages globally rather than in a virtual environment.
  - The ```--deploy``` flag ensures that the exact versions specified in Pipfile.lock are used, and the build will fail if Pipfile.lock is out of date or missing. As well it avoids install dev dependacies
4. Copy Application Code: Copy the rest of your application code to the Docker container.
5. Set Environment Variables for Development: Set the necessary environment variables for the **development** and **production** environment.
6. Expose Port: Expose port 8000 for the application.
7. Run Development Server: Use the default Python environment to run Django's development server.


### Building the docker image

To build the Docker image for the chat application, use the following command:
```bash
docker build -t chat-app .
```

### Running the Docker Image

To run the Docker container, use:
```bash
docker run -p 8000:8000 --env-file .env chat-app
```
