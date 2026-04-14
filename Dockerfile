# Use the latest official Python image as a base image
FROM python:latest

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the uv installer
ADD https://astral.sh/uv/0.11.6/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Set the working directory in the container to /app
WORKDIR /app

# Copy the rest of the application code to the working directory
COPY . .

# Disable development dependencies
ENV UV_NO_DEV=1

RUN uv sync --locked

# git owo
RUN mkdir test && \
    cd test && \
    git clone https://github.com/orangci/takina && \
    cp -r takina/.git ../.git && \
    cd .. && \
    rm -rf test

# Specify the command to run the application
CMD ["uv", "run", "takina"]
