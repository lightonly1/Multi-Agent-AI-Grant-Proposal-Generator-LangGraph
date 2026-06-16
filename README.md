# AI Research Grant Proposal Generator & Evaluator

[![Tech Stack: LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![LLM: Ollama / GPT-4o](https://img.shields.io/badge/Inference-Ollama%20%7C%20GPT--4o-blue.svg)](https://ollama.com/)
[![VectorDB: FAISS](https://img.shields.io/badge/Vector%20Store-FAISS-green.svg)](https://github.com/facebookresearch/faiss)
[![Backend: FastAPI / Streamlit](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Streamlit-red.svg)](https://fastapi.tiangolo.com/)

An enterprise-grade, privacy-focused **Agentic AI System** designed to automate the end-to-end generation, evaluation, and iterative refinement of rigorous academic and scientific research grant proposals. 

Developed as a flagship project within the **HYSEA Project Drona 2.0 track**, this architecture was successfully defended solo before a senior corporate executive evaluation panel from **TCS and Tech Mahindra**, receiving direct leadership commendations for system design, robust data extraction, and autonomous closed-loop execution.

---

##  Problem Statement & Business Context

### The Challenge
The development of research grant proposals is often hindered by the complexity of aligning diverse funding agency guidelines with intricate technical content and strict budgetary constraints. Researchers frequently struggle with compliance, structural formatting, and financial estimation, leading to high rejection rates.

### Industry Significance & Scoping
Securing research funding is a high-stakes, competitive necessity for both academic and industrial institutions. By standardizing the proposal drafting process and providing an objective, pre-submission scoring engine, this system:
* Minimizes compliance-driven human error.
* Drastically reduces manual preparation time.
* Increases the overall statistical probability of securing competitive grants across multiple deep-tech domains (e.g., Solar Energy, Material Science).

---

## 🛠️ System Architecture & Workflow

Unlike basic linear RAG pipelines or standard chatbots, this system leverages a **Multi-Agent StateGraph Architecture** powered by **LangGraph**. The workflow forms a closed feedback loop where the execution path is dynamically determined at runtime by an evaluation agent acting as an autonomous quality gate.
