#!/bin/bash

# Set variables (using .env file)
source .env

# Zip the function code (app.py, no dependencies)
zip -r9 function.zip lambda_function.py

# Deploy the function code to AWS Lambda (without user input)
aws lambda update-function-code \
  --function-name ${FUNCTION_NAME} \
  --zip-file fileb://function.zip

# clean up
rm function.zip