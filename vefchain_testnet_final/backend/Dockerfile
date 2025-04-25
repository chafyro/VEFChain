FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app

# Expose the port for the FastAPI app
EXPOSE 8000

# Run the application (adjust for your FastAPI app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]