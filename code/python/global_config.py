import os
import logging
from dotenv import load_dotenv
load_dotenv()

AI_ADVISOR_VERSION = "10.1.4"
LLM_MODEL = "gpt-4"
LOG_FILE_NAME = "aiadvisor.log"
LOG_LEVEL = logging.DEBUG
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME")
