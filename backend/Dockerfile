FROM python:3.10-slim

ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} HTTPS_PROXY=${HTTPS_PROXY}

WORKDIR /app

# Install system dependencies for jieba and document processing
RUN if [ -n "$HTTP_PROXY" ]; then \
        echo 'Acquire::http::Proxy "'$HTTP_PROXY'";' > /etc/apt/apt.conf.d/99proxy; \
    fi && \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/apt/apt.conf.d/99proxy

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