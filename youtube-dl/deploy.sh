#/!/bin/bash

# Set variables (using .env file)
source .env

# Echo variables
echo "BUCKET_NAME=$BUCKET_NAME"
echo "REGION=$REGION"

# Login to AWS ECR
aws ecr get-login-password \
  --region us-east-2 \
  | docker login \
    --username AWS \
    --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME

# Build the image
docker build --build-arg=BUCKET_NAME=$BUCKET_NAME \
  --build-arg=REGION=$REGION \
  -t youtube-dl .

# Tag the image
docker tag youtube-dl:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest
# Push the image
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# Deploy the image to AWS Lambda
aws lambda update-function-code \
  --function-name youtube-dl \
  --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# Delete untagged images from AWS ECR
IMAGES_TO_DELETE=$(aws ecr list-images \
  --repository-name $REPO_NAME \
  --filter "tagStatus=UNTAGGED" \
  --query 'imageIds[*]' \
  --output json)
aws ecr batch-delete-image \
  --repository-name $REPO_NAME \
  --image-ids "$IMAGES_TO_DELETE" || true

# clean up
docker system prune -a -f