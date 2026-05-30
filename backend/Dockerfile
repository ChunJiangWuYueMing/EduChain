FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for jieba and document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repository root so we can share one requirements file
# for both local development and container builds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY scripts/ /app/scripts/

# Create uploads directory
RUN mkdir -p uploads

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]