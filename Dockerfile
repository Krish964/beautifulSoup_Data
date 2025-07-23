# Use a lightweight official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project files into the container
COPY . .

# Expose port 5000 for the Flask app
EXPOSE 5000

# Command to run the flask app, make sure app.py runs the server on 0.0.0.0
CMD ["python", "app.py"]
