# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /no_caps

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    python3-dev \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test files
COPY no_caps/tests/ ./tests/
COPY pytest.ini .

# Set Python path
ENV PYTHONPATH=/no_caps


# Command to run tests
CMD ["pytest"]