# agents/guideline_agent.py

import os
import json
import logging

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class GuidelineIngestionAgent:

    def __init__(self, faiss_index_path: str = "data/faiss_index"):

        # FREE local embeddings (NO API)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.faiss_index_path = faiss_index_path

        # Text splitting
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )

    def load_and_chunk_pdf(self, pdf_path: str) -> list:

        logger.info(f"Loading PDF from: {pdf_path}")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found at path: {pdf_path}")

        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        logger.info(f"Loaded {len(pages)} pages from PDF")

        chunks = self.text_splitter.split_documents(pages)

        logger.info(f"Split into {len(chunks)} chunks")

        return chunks

    def build_faiss_index(self, chunks: list) -> FAISS:

        logger.info("Building FAISS index (LOCAL - FREE MODE)...")

        vectorstore = FAISS.from_documents(chunks, self.embeddings)

        os.makedirs(self.faiss_index_path, exist_ok=True)
        vectorstore.save_local(self.faiss_index_path)

        logger.info(f"FAISS index saved to: {self.faiss_index_path}")

        return vectorstore

    def extract_guidelines_structure(self, pages: list) -> dict:

        logger.info("Skipping LLM extraction (FREE MODE)")

        # Static fallback structure
        guidelines = {
            "proposal_sections": [
                "Title",
                "Abstract",
                "Problem Statement",
                "Objectives",
                "Methodology",
                "Expected Impact"
            ],
            "eligibility_criteria": [
                "Open to all researchers"
            ],
            "evaluation_rubric": {
                "innovation": 25,
                "feasibility": 25,
                "budget_clarity": 25,
                "impact": 25
            },
            "max_budget": None,
            "duration_months": 12,
            "funding_agency": "Unknown",
            "submission_deadline": None,
            "special_requirements": []
        }

        return guidelines

    def run(self, pdf_path: str) -> dict:

        logger.info("=== GuidelineIngestionAgent: Starting ===")

        # Step 1: Load and chunk PDF
        chunks = self.load_and_chunk_pdf(pdf_path)

        # Step 2: Build FAISS index
        self.build_faiss_index(chunks)

        # Step 3: Load full pages
        loader = PyPDFLoader(pdf_path)
        full_pages = loader.load()

        # Step 4: Get guidelines (static in free mode)
        guidelines = self.extract_guidelines_structure(full_pages)

        logger.info("=== GuidelineIngestionAgent: Done ===")

        return {
            "guidelines_summary": guidelines,
            "faiss_index_path": self.faiss_index_path,
            "chunk_count": len(chunks)
        }