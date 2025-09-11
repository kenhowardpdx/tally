# Use official Python image for a smaller footprint
FROM python:3.13-slim

# Set environment variables for a more robust and explicit setup.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install Poetry and the export plugin
RUN pip install --upgrade poetry poetry-plugin-export

# Copy only the necessary files for dependency installation to leverage Docker's layer cache
COPY pyproject.toml poetry.lock* /app/

# Export Poetry dependencies to a requirements.txt file and install them with pip
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip install -r requirements.txt

# Copy the rest of your application code
COPY . /app

# Expose the port your application will run on
EXPOSE 8000

# Command to run the application using Gunicorn and Uvicorn workers
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "src.main:app", "-b", "0.0.0.0:8000"]
