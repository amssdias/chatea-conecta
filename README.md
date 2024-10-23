[python-download]: https://www.python.org/downloads/
[redis-download]: https://redis.io/download/

![Workflow branch master](https://github.com/amssdias/chatea-conecta/actions/workflows/test.yml/badge.svg?branch=master)

![Python Badge](https://img.shields.io/badge/Python-3.9-blue?logo=python)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)
[![Docker](https://badgen.net/badge/icon/docker?icon=docker&label)](https://https://docker.com/)

<h1 align=center>Chatea Conecta</h1>

## :hammer: Getting started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Pre requisites

- [Python][python-download] - 3.9
- [Redis][redis-download]
- [Docker](https://www.docker.com/) (Optional)

### Installing


1. Clone this repository to your local machine
2. Navigate to the project directory


```
git clone https://github.com/amssdias/chatea-conecta.git
cd chatea-conecta
```
   
3. Make sure you have installed Redis with a password.



4. On the "redis.conf" you should write your redis password.


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
