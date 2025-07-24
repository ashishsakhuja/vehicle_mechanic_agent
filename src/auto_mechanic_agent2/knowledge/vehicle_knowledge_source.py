# src/auto_mechanic_agent2/knowledge/vehicle_knowledge_source.py

import os
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_pinecone.vectorstores import PineconeVectorStore
from langchain.docstore.document import Document

class ManualContentIndex:
    """
    Pinecone-backed index of all manuals in the knowledge folder.
    """

    def __init__(self):
        # load environment
        load_dotenv()
        api_key    = os.getenv("PINECONE_API_KEY")
        env        = os.getenv("PINECONE_ENV")
        index_name = os.getenv("PINECONE_INDEX")
        openai_key = os.getenv("OPENAI_API_KEY")
        if not (api_key and env and index_name and openai_key):
            raise ValueError(
                "Ensure PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX, and OPENAI_API_KEY are set in .env"
            )

        # init Pinecone client and index
        pc = Pinecone(api_key=api_key, environment=env)
        # create index if missing
        if index_name not in pc.list_indexes().names():
            pc.create_index(name=index_name, dimension=1536, metric="cosine")
        index = pc.Index(index_name)

        # init embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)

        # build PineconeVectorStore
        # text_key='page_content' maps Document.page_content
        self.vectorstore = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            text_key="page_content",
            pinecone_api_key=api_key,
            index_name=index_name,
        )

    def find_relevant_pages(self, query: str, k: int = 3):
        """
        Return up to k Documents most relevant to the query.
        """
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        return retriever.get_relevant_documents(query)