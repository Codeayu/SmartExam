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
    default-mysql-client \
    # Dependencies for PyMuPDF (fitz)
    libmupdf-dev \
    mupdf \
    mupdf-tools \
    libfreetype6-dev \
    # Additional dependencies that might be needed
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libxrender-dev \
    libffi-dev \
    # PDF generation tools
    wkhtmltopdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Install Python dependencies in two steps to handle complex packages better
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools && \
    # Install PyMuPDF separately first
    pip install PyMuPDF==1.23.7 && \
    # Then install the rest of the dependencies
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Add database configuration wrapper
RUN echo 'import os\nimport pymysql\npymysql.install_as_MySQLdb()' > database_wrapper.py

# Make sure the static directory exists
RUN mkdir -p staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput || echo "Skipping collectstatic"

# Run the application
CMD gunicorn smartexam.wsgi:application --bind 0.0.0.0:$PORT