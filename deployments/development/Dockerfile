FROM python:3.9

WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

ENV DJANGO_SETTINGS_MODULE=chat_connect.settings.settings_development

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=chat_connect.settings.settings_development"]
