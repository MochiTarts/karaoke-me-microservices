#/!/bin/bash

# Set environment variables from .env file
export $(egrep -v '^#' .env | xargs)

# Login to AWS ECR
aws ecr get-login-password \
  --region us-east-2 \
  | docker login \
    --username AWS \
    --password-stdin 760755533050.dkr.ecr.us-east-2.amazonaws.com/youtube-dl

# Build the image
docker build -t youtube-dl .

# Tag the image
docker tag youtube-dl:latest 760755533050.dkr.ecr.us-east-2.amazonaws.com/youtube-dl:latest
# Push the image
docker push 760755533050.dkr.ecr.us-east-2.amazonaws.com/youtube-dl:latest

# Deploy the image to AWS Lambda
aws lambda update-function-code \
  --function-name youtube-dl \
  --image-uri 760755533050.dkr.ecr.us-east-2.amazonaws.com/youtube-dl:latest

# clean up
docker system prune -a -f