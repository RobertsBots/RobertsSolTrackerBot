# Use official Python image
FROM python:3.10.13-slim

# Set workdir
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all files
COPY . .

# Expose port for FastAPI
EXPOSE 8000

# Start command for Render (FastAPI app)
CMD ["python", "main.py"]
