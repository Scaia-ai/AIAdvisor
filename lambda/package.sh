#!/bin/bash
# Prepares a zip for deploying to AWS Lambda
# Argument: lambda_name, such as 'fastapi'
# Check if the argument is provided
if [ -z "$1" ]; then
  echo "Error: No directory provided."
  exit 1
fi
# Change to the directory provided in the argument
cd "$1" || exit 2
rm -fr lambda_package
mkdir lambda_package && cd lambda_package
pip install -r ../requirements.txt -t .
cp ../lambda_handler.py .
cp ../../../code/python/global_config.py .
cp ../../../code/python/main.py .
zip -q -r ../lambda_package.zip .
cd ..
aws s3 cp --profile scaia lambda_package.zip s3://scaia-lambda/lambda-package.zip
cd ..