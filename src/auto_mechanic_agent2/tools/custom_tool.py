# src/auto_mechanic_agent2/tools/custom_tool.py

import os
from typing import Any, Dict
from crewai.tools import BaseTool
from pydantic import Field
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from auto_mechanic_agent2.knowledge.vehicle_knowledge_source import ManualContentIndex

# ──────────────────────────────── Manual Q&A Tool ────────────────────────────────
class ManualQATool(BaseTool):
    name: str = Field(
        "manual_qa",
        description="Given a repair query, retrieve from our Pinecone index and answer"
    )
    description: str = Field(
        "A repair question → precise manual lookup + QA answer",
        description="What this tool does"
    )
    manual_index: ManualContentIndex = Field(
        default_factory=ManualContentIndex,
        description="Pinecone‑backed index for all PDF chunks"
    )
    top_k: int = Field(4, description="How many chunks to retrieve from Pinecone")
    model_name: str = Field("gpt-4.1-mini", description="OpenAI model to use")
    temperature: float = Field(0.0, description="LLM temperature")

    def _run(self, query: str) -> str:
        # 1) Retrieve the top‑k chunks from Pinecone
        retriever = self.manual_index.vectorstore.as_retriever(
            search_kwargs={"k": self.top_k}
        )

        # 2) Build a QA chain over those chunks
        llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
        )

        # 3) Run the chain and return the answer
        return qa.run(query)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError("ManualQATool does not support async.")


# ────────────────────────────── Parts Scraper Tool ──────────────────────────────
class PartsScraperTool(BaseTool):
    name: str = Field(
        "parts_scraper",
        description="Generate direct search URLs on Amazon, AutoZone, and O'Reilly for a given list of parts/tools.",
    )
    description: str = Field(
        "A comma-separated list of parts/tools → URLs",
        description="What this tool does"
    )

    def _run(self, parts_list: str) -> Dict[str, str]:
        from urllib.parse import quote_plus
        keywords = " ".join(p.strip() for p in parts_list.split(","))
        q = quote_plus(keywords)
        return {
            "amazon":   f"https://www.amazon.com/s?k={q}",
            "autozone": f"https://www.autozone.com/searchresult?searchText={q}",
            "oreilly":  f"https://www.oreillyauto.com/search?q={q}"
        }

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError("PartsScraperTool does not support async.")
