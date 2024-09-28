# Use the latest official Python image as a base image
FROM python:latest

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY requirements.txt ./

# Install pip and the Python dependencies listed in requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# git owo
RUN mkdir test && \
    cd test && \
    git clone https://github.com/orxngc/takina && \
    cp -r takina/.git ../.git && \
    cd .. && \
    rm -rf test

# Specify the command to run the application
CMD ["python3", "takina"]
