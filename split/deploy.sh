#/!/bin/bash

# Set variables (using .env file)
source .env

echo $BUCKET_NAME
echo $CONNECTIONS_TABLE_NAME
echo $REGION

# Login to AWS ECR
aws ecr get-login-password \
  --region $REGION \
  | docker login \
    --username AWS \
    --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME

# Print environment variables
echo "BUCKET_NAME: $BUCKET_NAME"
echo "CONNECTIONS_TABLE_NAME: $CONNECTIONS_TABLE_NAME"
echo "REGION: $REGION"

# Build the image (with environment variables)
docker build --build-arg=BUCKET_NAME=$BUCKET_NAME \
  --build-arg=CONNECTIONS_TABLE_NAME=$CONNECTIONS_TABLE_NAME \
  --build-arg=REGION=$REGION \
  -t split-audio:latest .

# Tag the image
docker tag split-audio:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest
# Push the image
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# Deploy the image to AWS Lambda
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# clean up
docker system prune -a -f