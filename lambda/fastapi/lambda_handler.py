from aws_lambda_fastapi import FastAPILambda
from main import app # Assuming your FastAPI app is defined in main.py
lambda_handler = FastAPILambda(app)