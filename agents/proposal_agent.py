# agents/proposal_agent.py

import os
import json
import logging

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class ProposalDraftingAgent:

    def __init__(self):
        # FREE embeddings (same as guideline agent)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def load_retriever(self, faiss_index_path: str, k: int = 5):

        vectorstore = FAISS.load_local(
            faiss_index_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        return vectorstore.as_retriever(search_kwargs={"k": k})

    def retrieve_relevant_context(self, retriever, topic: str) -> str:

        docs = retriever.invoke(topic)

        context = "\n\n---\n\n".join([doc.page_content for doc in docs])

        logger.info(f"Retrieved {len(docs)} context chunks")

        return context

    def generate_all_sections(self, topic: str, context: str) -> dict:

        logger.info("Generating proposal (FREE MODE)...")

        # SIMPLE LOCAL GENERATION (NO LLM)
        proposal = {
            "Title": f"AI-Based Research on {topic}",

            "Abstract": f"""
This research focuses on {topic} using artificial intelligence techniques.
The aim is to improve efficiency, performance, and scalability using data-driven methods.
""",

            "Problem Statement": f"""
Current systems in {topic} suffer from inefficiencies and lack of optimization.
There is a need for intelligent solutions that can analyze data and improve outcomes.
""",

            "Objectives": """
1. Analyze current challenges
2. Develop AI-based models
3. Optimize system performance
4. Validate results using real-world data
""",

            "Methodology": f"""
- Data collection and preprocessing
- Model development using machine learning
- Training and validation
- Performance evaluation and optimization
""",

            "Expected Impact": f"""
This research will improve efficiency in {topic}, reduce costs,
and provide scalable intelligent solutions for future applications.
"""
        }

        return proposal

    def run(
        self,
        topic: str,
        faiss_index_path: str,
        guidelines_summary: dict,
        eval_scores: dict = None
    ) -> dict:

        logger.info("=== ProposalDraftingAgent: Starting ===")

        retriever = self.load_retriever(faiss_index_path)

        context = self.retrieve_relevant_context(retriever, topic)

        proposal = self.generate_all_sections(topic, context)

        logger.info("=== ProposalDraftingAgent: Done ===")

        return {"proposal_draft": proposal}