#!/bin/bash

# Generate SSH key if it doesn't exist
if [ ! -f id_pretix_enterprise ]; then
    echo "Generating SSH key..."
    ssh-keygen -N "" -f id_pretix_enterprise
    echo -e "\nYour public SSH key is:\n"
    cat id_pretix_enterprise.pub
    echo -e "\nPlease send this public key to your pretix sales representative."
    echo "Once they confirm the key is configured, press Enter to continue..."
    read
else
    echo "SSH key already exists."
fi

# Build Docker image
echo "Building Docker image..."
docker build -t pretix-rollno . || {
    echo "Error: Docker build failed"
    exit 1
}

echo -e "\nDocker image built successfully!"
echo "You can now run pretix with:"
echo "docker run -p 8000:80 pretix-rollno" 