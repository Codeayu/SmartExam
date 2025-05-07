FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    python3-dev \
    libssl-dev \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Install Python dependencies in stages to isolate potential issues
COPY requirements.txt .

# Install Python packages one by one to isolate problematic packages
RUN pip install --upgrade pip setuptools wheel && \
    pip install gunicorn whitenoise python-dotenv dj-database-url && \
    pip install Django==4.2.11 django-simple-captcha==0.5.18 && \
    pip install Pillow==10.0.0 reportlab==4.0.4 && \
    pip install pymysql==1.1.0 && \
    pip install psycopg2-binary==2.9.9 && \
    pip install requests==2.32.3 xhtml2pdf==0.2.11 && \
    pip install --no-deps google-api-core==2.24.2 google-api-python-client==2.168.0 && \
    pip install --no-deps google-auth==2.39.0 google-auth-httplib2==0.2.0 google-genai==1.12.1 && \
    pip install -r requirements.txt --no-deps

# Copy project files
COPY . .

# Add database configuration wrapper
RUN echo 'import os\nimport pymysql\npymysql.install_as_MySQLdb()' > database_wrapper.py

# Create necessary directories
RUN mkdir -p staticfiles media

# Collect static files
RUN python manage.py collectstatic --noinput || echo "Skipping collectstatic"

# Run the application
CMD gunicorn smartexam.wsgi:application --bind 0.0.0.0:$PORT