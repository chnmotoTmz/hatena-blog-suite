import os
import re
from typing import List, Dict, Optional, Tuple
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import chromadb
from chromadb.config import Settings
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class RetrievalAgent:
    def __init__(self, openai_api_key: str, chroma_persist_dir: str = "./chroma_db"):
        self.openai_api_key = openai_api_key
        self.chroma_persist_dir = chroma_persist_dir
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            temperature=0.7,
            model_name="gpt-4"
        )
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def create_vectorstore_from_articles(self, articles: List[Dict]):
        documents = []
        
        for article in articles:
            content = article.get('full_content', '') or article.get('summary', '')
            if not content:
                continue
                
            metadata = {
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'date': article.get('date', ''),
                'categories': ', '.join(article.get('categories', [])),
                'word_count': article.get('word_count', 0)
            }
            
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)
        
        split_documents = self.text_splitter.split_documents(documents)
        
        self.vectorstore = Chroma.from_documents(
            documents=split_documents,
            embedding=self.embeddings,
            persist_directory=self.chroma_persist_dir
        )
        self.vectorstore.persist()
        
    def find_related_articles(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Create or load it first.")
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results