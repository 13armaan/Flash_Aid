# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only requirements
COPY requirements.txt .

# Install only lightweight dependencies (ctranslate2 without torch)
RUN pip install --no-cache-dir --only-binary=:all: --no-deps ctranslate2==4.3.1 \
    && grep -v "ctranslate2" requirements.txt > req.txt \
    && pip install --no-cache-dir -r req.txt

# Copy source code
COPY src/ ./src/

# Run your main app
CMD ["python", "-m", "src.main"]

