# AI Research Grant Proposal Generator & Evaluator
### M.Tech Capstone Project — Vignan Institute of Technology and Science
**Author:** Krit Prakash | M.Tech (CSE) | Roll No: [Your Roll No]  
**Guide:** [Your Guide's Name] | Department of Computer Science  
**Academic Year:** 2024–25

---

## Overview

This project builds an **Agentic AI system** that automates the end-to-end
research grant proposal writing process. Given a research topic and a funding
guideline PDF, the system:

1. Reads and understands the funding guidelines (RAG over PDF)
2. Generates a complete 6-section research proposal
3. Creates a realistic research budget and project timeline
4. Evaluates the proposal against a 4-criterion rubric
5. Automatically refines weak sections until the target quality is reached

The system uses **LangGraph** to orchestrate agents in a closed feedback loop —
a core demonstration of Agentic AI behavior vs. a simple chatbot.

---

## Project Structure

```
grant_proposal_ai/
│
├── agents/                     # The five core agents
│   ├── guideline_agent.py      # Agent 1: PDF ingestion + FAISS indexing
│   ├── proposal_agent.py       # Agent 2: RAG-based proposal generation
│   ├── budget_agent.py         # Agent 3: Budget + timeline generation
│   ├── evaluation_agent.py     # Agent 4: Rubric-based scoring
│   └── refinement_agent.py     # Agent 5: Feedback-driven refinement
│
├── graph/                      # LangGraph wiring
│   ├── state.py                # ProposalState TypedDict (shared state)
│   ├── nodes.py                # Node functions (LangGraph adapters)
│   ├── edges.py                # Conditional edge routing logic
│   └── build_graph.py          # StateGraph assembly + compile
│
├── db/
│   └── storage.py              # SQLite CRUD operations
│
├── utils/
│   └── exporters.py            # .docx and .txt export
│
├── tests/
│   └── test_agents.py          # Unit tests (pytest, no API key needed)
│
├── app.py                      # Streamlit web UI
├── run_graph.py                # CLI runner (for testing without Streamlit)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Technology Stack

| Component | Library | Purpose |
|---|---|---|
| LLM calls | `langchain-openai` | GPT-4o for all agent tasks |
| Agent orchestration | `langgraph` | StateGraph with conditional routing |
| PDF parsing | `pypdf` via `langchain-community` | Load and chunk guideline PDFs |
| Vector store | `faiss-cpu` | Local RAG — no cloud vector DB needed |
| Web UI | `streamlit` | Demo interface |
| Database | `sqlite3` (stdlib) | Persistent storage of all runs |
| Export | `python-docx` | .docx proposal download |
| Testing | `pytest` | Offline unit tests (mocked LLM) |

---

## Setup Instructions

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd grant_proposal_ai
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

```bash
cp .env.example .env
# Edit .env and add your key:
# OPENAI_API_KEY=sk-your-key-here
```

Or set it directly:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### 4. Or use the CLI runner

```bash
python run_graph.py \
  --topic "AI-assisted early detection of diabetic retinopathy" \
  --pdf path/to/guidelines.pdf \
  --max-iter 3 \
  --threshold 75
```

### 5. Run tests (no API key needed)

```bash
python -m pytest tests/ -v
```

---

## How the Agents Work

### Agent 1 — Guideline Ingestion Agent (`guideline_agent.py`)
- Loads the PDF using `PyPDFLoader`
- Splits into 1000-character chunks with 150-character overlap
- Embeds chunks and saves a **FAISS index** to `data/faiss_index/`
- Uses GPT-4o (temperature=0) to extract structured guidelines:
  proposal sections, eligibility, rubric weights, budget limits

### Agent 2 — Proposal Drafting Agent (`proposal_agent.py`)
- Loads the FAISS index and retrieves top-5 relevant chunks for the topic
- Generates all 6 sections in **one LLM call** (for coherence)
- Temperature=0.7 for creative, well-written output
- On re-drafts, adds evaluation feedback to the prompt automatically

### Agent 3 — Budget & Timeline Agent (`budget_agent.py`)
- Reads the Methodology section to infer resource needs
- Generates itemized budget with category + justification per line
- Creates month-by-month milestone timeline
- Validates total against guideline budget limit

### Agent 4 — Evaluation Agent (`evaluation_agent.py`)
- Scores 4 criteria (Innovation, Feasibility, Budget Clarity, Impact) × 25 pts
- Temperature=0.1 for consistent, reproducible scoring
- Returns structured JSON with per-criterion strength + weakness
- Corrects LLM arithmetic errors (verifies `total_score = sum of criteria`)

### Agent 5 — Refinement Agent (`refinement_agent.py`)
- Identifies which criteria scored below threshold (18/25)
- Uses GPT-4o to synthesize weaknesses into an actionable refinement brief
- Triggers **full proposal regeneration** (not section patching) for coherence
- Re-draft prompt includes both raw weaknesses and the synthesized brief

---

## LangGraph Workflow

```
START
  → ingest_guidelines      (runs once)
  → draft_proposal         (initial draft)
  → generate_budget        (initial budget)
  → evaluate_proposal      (score + feedback)
  → [should_refine?]
       score >= threshold OR max_iter reached → finalize_output → END
       score < threshold AND iterations left  → refine_proposal
                                                     → evaluate_proposal  ↑
                                                     (loop continues)
```

The `should_refine` **conditional edge** is what makes this agentic —
the graph's execution path is determined at runtime by the evaluation output,
not hardcoded by the programmer.

---

## Database Schema

SQLite database at `data/proposals.db`:

```sql
runs         (id, topic, pdf_path, started_at, finished_at, final_score, total_iterations, status)
proposals    (id, run_id, iteration, version_tag, title, abstract, ..., full_draft_json)
evaluations  (id, run_id, proposal_id, iteration, innovation_score, ..., total_score, grade)
budgets      (id, run_id, proposal_id, total_cost_usd, within_limit, full_budget_json)
```

Every iteration is saved — you can compare how the proposal improved over rounds.

---

## Why This Is Agentic AI (Not Just a Chatbot)

| Property | Simple Chatbot | This System |
|---|---|---|
| Waits for user each step | Yes | No — runs autonomously |
| Has a goal to pursue | No | Yes: achieve score ≥ threshold |
| Makes routing decisions | No | Yes: conditional edge routing |
| Uses external tools | Rarely | Yes: PDF, FAISS, SQLite, API |
| State persists across steps | No | Yes: `ProposalState` TypedDict |
| Can loop on its own output | No | Yes: eval → refine → eval loop |

---

## Sample Output

```
=============================================================
  PIPELINE COMPLETE
=============================================================
  Final score:  82/100  (Grade: A)
  Iterations:   2
  Budget total: $28,200 USD
=============================================================

── EVALUATION SCORES ──
  Innovation           20/25  | weakness: Ensemble novelty not justified...
  Feasibility          22/25  | weakness: IRB approval not mentioned...
  Budget Clarity       19/25  | weakness: Cloud credits need breakdown...
  Impact               21/25  | weakness: International scale unsubstantiated...
```

---

## Known Limitations & Future Work

- **API cost**: Each full pipeline run uses ~8–12 LLM calls. At gpt-4o pricing,
  roughly $0.10–0.25 per run. Use `--max-iter 1` during development.

- **PDF quality**: Works best on text-based PDFs. Scanned image PDFs need OCR
  (not implemented — would add `pytesseract`).

- **Budget in INR**: Currently generates USD amounts. A future version should
  detect the funding agency's currency from the guideline text.

- **Async execution**: Budget generation could run in parallel with parts of
  proposal drafting. LangGraph supports async — would add with `graph.ainvoke()`.

- **Human-in-the-loop**: A reviewer approval step between evaluate and refine
  would make the system production-ready. LangGraph supports this via
  `interrupt_before` parameter on `graph.compile()`.

---

## References

1. LangGraph Documentation — https://langchain-ai.github.io/langgraph/
2. LangChain RAG Tutorial — https://python.langchain.com/docs/use_cases/question_answering/
3. FAISS: Efficient Similarity Search — Johnson et al., 2019
4. ReAct: Synergizing Reasoning and Acting in LLMs — Yao et al., 2022
5. DST-SERB Grant Guidelines — https://serb.gov.in/page/english/core_research_grant
