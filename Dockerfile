FROM python:3.11-slim

# Configure Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# Create a non-root user with UID 1000 for Hugging Face Spaces
RUN useradd -m -u 1000 user

WORKDIR /home/user/app

# Install dependencies with caching optimization
COPY --chown=user:user backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files (creditcard.csv and caches excluded via .dockerignore)
COPY --chown=user:user . .

# Ensure data directory exists and has write permissions for SQLite persistence
RUN mkdir -p backend/data && chown -R user:user /home/user/app

USER user

# Hugging Face Spaces listens on port 7860
EXPOSE 7860

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
