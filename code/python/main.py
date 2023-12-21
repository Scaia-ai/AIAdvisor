# Main for CasifyAI code


import asyncio
from logging import StreamHandler
import assemblyai as aai
import threading
import time
import os
import traceback
from fastapi import FastAPI, UploadFile, Form
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from casify_pinecone_lch import clean_namespace
from store_document import do_store_document
from fastapi import HTTPException
from global_config import CASIFY_AI_VERSION
import logging
import openai
from langchain.vectorstores import Pinecone
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv, find_dotenv
import pinecone
from typing import Optional
from fastapi import FastAPI, Query
from langchain.llms import OpenAI
import shutil
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIAdvisor")

model = "gpt-4"
default_index_name = os.getenv("PINECONE_INDEX_NAME")

# Create a file handler which logs even debug messages
log_file = 'aiadvisor.log'
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(fh)

# Example logging
logger.info("Logger is configured to write to a file: " + log_file)

_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.getenv('OPENAI_API_KEY')

app = FastAPI(
    title="CasifyAI API",
    description="Talk to ChatGPT and Pinecone using Langchain",
    version=CASIFY_AI_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    question: str
    case_id: str


@app.get("/question_case/", summary="Ask CasifyAI about your case")
async def ask_question(question: str, case_id: str):
    try:
        logger.info("****************ask question")
        logger.info(f"Question: {threading.active_count()}")
        _ = load_dotenv(find_dotenv())  # read local .env file
        openai.api_key = os.getenv('OPENAI_API_KEY')

        namespace = case_id
        logger.info("namespace=" + namespace)
        # initialize pinecone
        pinecone.init(
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT')
        )
        logger.info("pinecone.init OK")
        from langchain.embeddings.openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)

        def get_similar_docs(query, namespace, num_sources=10, score=False):
            index = Pinecone.from_existing_index(default_index_name, embeddings, namespace=namespace)
            if score:
                similar_docs = index.similarity_search_with_score(query, k=num_sources, namespace=namespace)
            else:
                similar_docs = index.similarity_search(query, k=num_sources, namespace=namespace)
            logger.info(str(len(similar_docs)) + " similar docs found")
            return similar_docs

        def get_answer(query, namespace):
            from langchain.llms import OpenAI
            llm = OpenAI(model_name=model)
            chain = load_qa_chain(llm, chain_type="stuff")
            similar_docs_list = get_similar_docs(query, namespace=namespace)
            return chain.run(input_documents=similar_docs_list, question=query)

        my_query = str(question)
        logger.info("my_query=" + my_query)
        answer = get_answer(my_query, namespace)
        print(answer)

        logger.info("A: " + answer)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")
    return {"question": question, "answer": answer}


@app.get("/question_cases/", summary="Ask CasifyAI about your multiple cases")
async def ask_question(question: str, case_ids: list[str] = Query(...)):
    def get_similar_docs(query, namespace, num_sources=10, score=False):
        index = Pinecone.from_existing_index(default_index_name, embeddings, namespace=namespace)
        if score:
            similar_docs = index.similarity_search_with_score(query, k=num_sources, namespace=namespace)
        else:
            similar_docs = index.similarity_search(query, k=num_sources, namespace=namespace)
        logger.info(str(len(similar_docs)) + " similar docs found")
        logger.info(type(similar_docs))
        return similar_docs

    def get_answer(query, namespace):
        combined_list = []
        for case_id in case_ids:
            namespace = case_id
            logger.info("namespace=" + namespace)
            llm = OpenAI(model_name=model)
            chain = load_qa_chain(llm, chain_type="stuff")
            similar_docs_list = get_similar_docs(query, namespace=namespace)
            combined_list.extend(similar_docs_list)

        return chain.run(input_documents=combined_list, question=query)

    try:
        logger.info("********** ask question about cases " + str(case_ids))
        logger.info(f"Start Question: {threading.active_count()}")
        _ = load_dotenv(find_dotenv())  # read local .env file
        openai.api_key = os.getenv('OPENAI_API_KEY')
        for case_id in case_ids:
            namespace = case_id
            logger.info("namespace=" + namespace)
            # initialize pinecone
            pinecone.init(
                api_key=os.getenv('PINECONE_API_KEY'),
                environment=os.getenv('PINECONE_ENVIRONMENT')
            )
            logger.info("pinecone.init OK")
            from langchain.embeddings.openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
            my_query = str(question)
            logger.info("my_query=" + my_query)
            answer = get_answer(my_query, namespace)
            print(answer)

            logger.info("A: " + answer)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")
    return {"question": question, "answer": answer}


@app.post("/clean_case_index/", status_code=201, summary="Clean up an index for a case")
async def clean_case_index(case_id: str):
    logger.info("Prepare index for case_id: " + case_id)
    clean_namespace(case_id)
    return {"message": "Index prepared successfully"}


@app.post("/store_document/", status_code=201, summary="Store a document for a case")
async def store_document(case_id: str = Form(...), document: UploadFile = Form(...)):
     try:
        logger.info("****************store document")
        logger.info(f"Start: {threading.active_count()}")
        content = await document.read()  # Read the file content
        content = content.decode()  # If the file is a text file, convert bytes to string
        doc_length = len(content)
        logger.info("Store a document of length: " + str(doc_length) + " for case: " + str(case_id))
        logger.info(f"Before Store Documents: {threading.active_count()}")
        number_splits = do_store_document(content, case_id);
        return {"message": "Document stored successfully", "Number of splits": str(number_splits)}
     except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")


@app.post("/store_content/", status_code=201, summary="Store document content for a case")
async def store_content(case_id: str = Form(...), content: str = Form(...)):
    doc_length = len(content)
    logger.info("Store content of length: " + str(doc_length) + " for case: " + str(case_id))
    number_splits = do_store_document(content, case_id)
    return {"message": "Content stored successfully", "Number of splits": str(number_splits)}


@app.get("/describe_index/", summary="Describe full Pinecone index (may take a long time)")
async def describe_index(index_name: Optional[str] = None):
    try:
        if index_name is None:
            index_name = default_index_name
        logger.info("Describing index: " + index_name)
        pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENVIRONMENT'))
        index = pinecone.Index(index_name)
        index_stats_response = index.describe_index_stats()
        one_string = str(index_stats_response)
        return {"index_stats": one_string}
    except Exception as e:
        logger.exception(e)

@app.post("/transcribe_audio/", status_code=200, summary="Transcribe an audio file")
async def transcribe(document: UploadFile = Form(...)):
    # Load API key from .env file
    _ = load_dotenv(find_dotenv())
    aai.settings.api_key = os.getenv('ASSEMBLY_AI_KEY')

    # Ensure API key is available
    if aai.settings.api_key is None:
        raise HTTPException(status_code=500, detail="API key not found")

    transcriber = aai.Transcriber()

    # Create a temporary directory to save the file
    temp_dir = Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / document.filename

    # Save the uploaded file to a temporary file
    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(document.file, buffer)

    # Transcribe the audio file
    try:
        transcript = transcriber.transcribe(str(temp_file))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup: remove the temporary file
        temp_file.unlink()

    return JSONResponse(content={"transcription": transcript.text})
    # return transcript.text

@app.get("/")
async def read_root():
    logger.info("Hello! Redirecting to /doc")
    return RedirectResponse(url='/docs')
