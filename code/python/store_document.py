import asyncio
import logging
import os
import threading
import openai
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import pinecone
from langchain.docstore.document import Document
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger("AIAdvisor")

num_splits = 0

def split_docs(documents, chunk_size=10, chunk_overlap=10):
    logger.info("split_docs with " + str(chunk_size) + " and " + str(chunk_overlap))
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(documents)
    global num_splits
    num_splits = len(docs)
    return docs

def find_long_strings(documents, max_length=40000):
    """Find strings in the array longer than a specified length."""
    return [s for s in documents if len(s.page_content) > max_length]


def split_string(input_string, chunk_size=20000):
    """Split a string into chunks of a specified size."""
    return [input_string[i:i + chunk_size] for i in range(0, len(input_string), chunk_size)]


def filter_strings(documents, max_length=40000):
    """Filter strings from the array based on length."""
    return [s for s in documents if len(s.page_content) <= max_length]


def do_store_document(content: str, namespace: str, filename: str):
    logger.info("do_store_document ")
    logger.info("namespace: " + namespace)
    temp_file = os.path.join("/tmp", "temp.txt")
    with open(temp_file, 'w') as f:
        f.write(content)

    _ = load_dotenv(find_dotenv())  # read local .env file
    openai.api_key = os.getenv('OPENAI_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME')
    pinecone.init(
        api_key=os.getenv('PINECONE_API_KEY'),
        environment=os.getenv('PINECONE_ENVIRONMENT')
    )
    logger.info(f"Init Pinecone: {threading.active_count()}")
    loader = TextLoader(temp_file)
    documents = loader.load()
    docs = split_docs(documents)
    long_strings = find_long_strings(docs)
    docs = filter_strings(docs)
    logger.info(f"Long strings {str(len(long_strings))}")

    for value in long_strings:
        splitted_strings = split_string(value.page_content)
        for txt in splitted_strings:
            new_doc = Document(page_content=txt)
            docs.append(new_doc)

    source = f"[[Source: {filename}]]"
    logger.info(f"Source: {source}")

    for document in docs:
        document.page_content = f"{source} {document.page_content}" 

    logger.info("Document split into " + str(len(docs)) + " paragraphs completed")
    embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
    Pinecone.from_documents(docs, embeddings, index_name=index_name, namespace=namespace)
    os.remove(temp_file)
    return str(len(docs))