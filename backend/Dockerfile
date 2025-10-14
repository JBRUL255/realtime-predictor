# Use lightweight Python image
FROM python:3.11-slim

# Prevent prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for Playwright (Chromium)
RUN apt-get update && apt-get install -y \
    wget ca-certificates gnupg \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpangocairo-1.0-0 \
    libasound2 libxss1 fonts-liberation libgtk-3-0 libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy everything from backend folder (where Dockerfile lives) into /app
COPY . .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright browser binaries
RUN playwright install --with-deps chromium

# Expose backend port
EXPOSE 8000

# Run the FastAPI app via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
