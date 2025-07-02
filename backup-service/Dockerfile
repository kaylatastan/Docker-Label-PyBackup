FROM python:3.9-slim

# Install system dependencies including mysql-client for mysqldump
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY backup_manager.py .

# Make backup manager executable
RUN chmod +x backup_manager.py

# Create backups directory
RUN mkdir -p /app/backups

# Run the backup service
CMD ["python", "app.py"]