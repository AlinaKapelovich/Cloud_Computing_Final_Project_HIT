# MedCloud container image.
# Docker packages the app + all its dependencies so it runs the same everywhere
# ("a small local cloud"). Think of the image as a template and the container as a
# running instance of it.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

WORKDIR /app

# tesseract-ocr provides the local OCR fallback used when no cloud OCR key is set.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

# Create runtime directories for uploads and generated PDFs.
RUN mkdir -p uploads generated_pdfs

EXPOSE 5000

# Gunicorn is the production WSGI server. It binds to $PORT (Render sets this).
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 run:app"]
