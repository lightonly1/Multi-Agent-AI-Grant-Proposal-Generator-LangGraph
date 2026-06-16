# app.py
# Streamlit UI — AI Research Proposal Generator 
import os
import tempfile
import streamlit as st
import plotly.graph_objects as go

from run_graph import run_pipeline

# ── PAGE SETUP ─────────────────────────────────────────────

st.set_page_config(
    page_title="AI Research Proposal Generator",
    layout="wide"
)

# ── HEADER ────────────────────────────────────────────────

st.title("AI-Based Research Proposal Generator")

st.markdown("""
This application generates structured research proposals from guideline documents.

Upload a PDF and enter a topic. The system will:
- understand the guidelines
- generate a proposal
- create a budget plan
- evaluate the proposal quality

The goal is to simplify proposal writing and make it more structured and accessible.
""")

# ── INPUT SECTION ─────────────────────────────────────────

st.subheader("Provide Inputs")

col1, col2 = st.columns(2)

with col1:
    topic = st.text_input("Enter research topic")

with col2:
    uploaded_file = st.file_uploader(
        "Upload guideline document (PDF)",
        type=["pdf"]
    )

run_button = st.button("Generate Proposal")

# ── PROCESSING ────────────────────────────────────────────

if run_button:

    if not topic:
        st.error("Please enter a research topic")

    elif not uploaded_file:
        st.error("Please upload a guideline document")

    else:
        with st.spinner("Processing the request. Please wait..."):

            # Save uploaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                pdf_path = tmp.name

            # Run pipeline
            final_state = run_pipeline(
                topic=topic,
                pdf_path=pdf_path,
                max_iterations=3,
                score_threshold=75
            )

        st.success("Proposal generated successfully")

        # ── OUTPUT ───────────────────────────────────────

        proposal = final_state.get("proposal_draft", {})
        budget = final_state.get("budget_timeline", {})
        eval_data = final_state.get("eval_scores", {})

        col1, col2 = st.columns([2, 1])

        with col2:
            st.metric("Final Score", eval_data.get("total_score", 0))
            st.write("Grade:", eval_data.get("grade", "N/A"))

        # ── PROPOSAL ────────────────────────────────────

        st.subheader("Generated Proposal")

        for key, value in proposal.items():
            st.markdown(f"**{key}**")
            st.write(value)

        # ── BUDGET ──────────────────────────────────────

        st.subheader("Budget Plan")

        if "budget_items" in budget:
            for item in budget["budget_items"]:
                st.write(
                    f"- {item['item']} ({item['category']}): "
                    f"${item['cost_usd']} — {item['justification']}"
                )

        # ── EVALUATION ─────────────────────────────────

        st.subheader("Evaluation Summary")

        if "criteria" in eval_data:
            for crit, details in eval_data["criteria"].items():
                st.markdown(f"**{crit.replace('_', ' ').title()}**")
                st.write(f"Score: {details.get('score', 0)}")
                st.write(f"Reason: {details.get('reason', '')}")
                st.write(f"Strength: {details.get('strength', '')}")
                st.write(f"Improvement: {details.get('weakness', '')}")
                st.markdown("---")

        # ── VISUALIZATION ───────────────────────────────

        if "criteria" in eval_data:
            labels = []
            scores = []

            for k, v in eval_data["criteria"].items():
                labels.append(k.replace("_", " ").title())
                scores.append(v.get("score", 0))

            fig = go.Figure()
            fig.add_trace(go.Bar(x=labels, y=scores))

            fig.update_layout(
                title="Evaluation Scores",
                xaxis_title="Criteria",
                yaxis_title="Score"
            )

            st.plotly_chart(fig, use_container_width=True)

        # ── FINAL NOTE ──────────────────────────────────

        st.markdown("""
The proposal is generated based on the uploaded guidelines and evaluated across key criteria such as innovation, feasibility, budget clarity and expected impact.

This allows quick assessment of proposal quality and highlights areas for improvement.
""")