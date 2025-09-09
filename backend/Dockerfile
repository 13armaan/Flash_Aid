# Use slim Python image
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install CPU-only PyTorch first
RUN pip install --upgrade pip \
 && pip install --no-cache-dir \
    torch==2.5.0+cpu torchvision==0.20.0+cpu torchaudio==2.5.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install all other Python packages

RUN pip install --no-cache-dir -r requirements.txt \
 && python -m pip show uvicorn


# Copy code

COPY . .



# Expose both FastAPI and Streamlit ports
EXPOSE 8000 8501
# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH=/app

# Railway-compatible CMD: uses $PORT env variable or defaults to 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]


