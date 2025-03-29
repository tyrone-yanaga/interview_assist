FROM python:3.9-slim

WORKDIR /no_caps

RUN apt-get update && apt-get install -y ffmpeg
# Install system dependencies - with explicit error checking
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
        python3-dev \
        build-essential \
        libffi-dev \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/* \
        && which ffmpeg || (echo "FFMPEG NOT INSTALLED CORRECTLY" && exit 1)

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/no_caps

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY no_caps/ .
COPY pytest.ini .

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]