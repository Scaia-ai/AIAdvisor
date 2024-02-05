import os
import logging
from dotenv import load_dotenv
load_dotenv()

AI_ADVISOR_VERSION = "10.2.3"
LLM_MODEL = "gpt-4-1106-preview"
LOG_FILE_NAME = "aiadvisor.log"
LOG_LEVEL = logging.DEBUG
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME")
