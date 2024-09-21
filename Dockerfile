FROM python:latest

# Set the working directory for the container
WORKDIR /app

# Install git to clone the repository
RUN apt-get update && apt-get install -y git

# Navigate to the repository folder
WORKDIR /app

# Install the dependencies from requirements.txt
RUN pip install -r requirements.txt

# Set the default command to run the app
CMD ["python3", "takina"]
