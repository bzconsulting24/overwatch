FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system deps if needed; add ffmpeg/openface deps here when required.
COPY behaviorAnalysis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY behaviorAnalysis/ .

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
