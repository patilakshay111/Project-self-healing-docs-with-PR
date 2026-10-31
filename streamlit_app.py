# streamlit_app.py: Streamlit UI for the self-healing docs pipeline
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import run_pipeline, print_results
from config import OPENAI_API_KEY

st.set_page_config(page_title="Self-Healing Docs", page_icon="📄", layout="wide")

st.title("📄 Self-Healing Technical Documentation")
st.caption("Detects stale docs from code changes and auto-generates fixes")

if not OPENAI_API_KEY:
    st.error("⚠️ OPENAI_API_KEY not set. Please copy .env.example to .env and add your API key.")
    st.stop()

col1, col2 = st.columns([3, 1])

with col1:
    repo_path = st.text_input("Repository path", value=".", help="Path to the codebase to analyze")
    docs_path = st.text_input("Docs path", value="docs", help="Path to the documentation directory")

with col2:
    st.write("")
    st.write("")
    run_button = st.button("🔍 Run Pipeline", type="primary")

if run_button:
    with st.spinner("Running self-healing docs pipeline..."):
        try:
            results = run_pipeline(repo_path=repo_path, docs_path=docs_path)
            st.success("Pipeline completed!")

            st.subheader("📊 Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Code Chunks", len(results["chunks"]))
            c2.metric("Doc Sections", len(results["sections"]))
            c3.metric("Links", len(results["links"]))
            c4.metric("Corrections", len(results["corrections"]))

            st.subheader("🔧 Changes Detected")
            for i, change in enumerate(results["changes"]):
                with st.expander(f"Change {i+1}: {change.file_path}"):
                    st.write(f"**Type:** {change.change_type}")
                    if change.old_code:
                        st.code(change.old_code[:500], language="diff")
                    if change.new_code:
                        st.code(change.new_code[:500], language="diff")

            st.subheader("✅ Corrections Generated")
            for i, correction in enumerate(results["corrections"]):
                with st.expander(f"Correction {i+1}: {correction.doc_section_id}"):
                    st.write(f"**Mode:** {correction.correction_mode}")
                    st.write(f"**Confidence:** {correction.confidence:.2f}")
                    st.write("**Original:**")
                    st.code(correction.original_content[:300])
                    st.write("**Corrected:**")
                    st.code(correction.corrected_content[:300])

        except Exception as e:
            st.error(f"Pipeline failed: {str(e)}")
