"""
This module provides functionality for
    finding similar documents in Pinecone index
    uses Langchain
    get ChatGPT answer from these documents

Functions:
-----------
    get_answer(query): gets an answer from ChatGPT
"""
import os
import openai
from dotenv import load_dotenv, find_dotenv
from pinecone import Pinecone
from langchain.vectorstores import Pinecone as Pinecone_lch
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import global_config
import logging


logger = logging.getLogger(global_config.LOG_FILE_NAME)

_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.getenv('OPENAI_API_KEY')
MODEL = "gpt-4"
index_name = os.getenv('PINECONE_INDEX_NAME')

# initialize pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))


embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
index_lch = Pinecone_lch.from_existing_index(index_name, embeddings, namespace = "159")


def get_similar_docs(query,namespace,num_sources=5,score=False):
  if score:
    similar_docs = index_lch.similarity_search_with_score(query, k=num_sources, namespace=namespace)
  else:
    similar_docs = index_lch.similarity_search(query,k=num_sources, namespace=namespace)
  return similar_docs


llm = OpenAI(model_name=MODEL)
chain = load_qa_chain(llm, chain_type="stuff")


def get_answer(query, namespace):
    similar_docs_list = get_similar_docs(query, namespace=namespace)
    # print(similar_docs)
    return chain.run(input_documents=similar_docs_list, question=query)


def clean_namespace(namespace: str):
    index_pc = Pinecone.Index(os.getenv('PINECONE_INDEX_NAME'))
    index_pc.delete(deleteAll=True, namespace=namespace)


def split_docs(documents, chunk_size=1000, chunk_overlap=20):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(documents)
    return docs



