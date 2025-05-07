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
    pip install google-api-core==2.11.0 google-api-python-client==2.84.0 && \
    pip install google-auth==2.17.3 google-auth-httplib2==0.1.0 && \
    pip install protobuf==4.23.0 googleapis-common-protos==1.59.0 && \
    pip install grpcio==1.54.0 && \
    pip install google-generativeai==0.3.1

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