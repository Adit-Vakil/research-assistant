"""Streamlit web UI for the multi-agent research assistant.

Run with:  streamlit run app.py
Reuses the existing orchestrator — no changes to the research pipeline.
"""
import asyncio
from datetime import datetime

import streamlit as st

from orchestrator import run_research

st.set_page_config(page_title="Research Assistant", page_icon="🔍", layout="centered")


def run_research_sync(query: str) -> dict:
    """Run the async pipeline from Streamlit's synchronous context (verbose off)."""
    return asyncio.run(run_research(query, verbose=False))


def report_to_markdown(result: dict) -> str:
    """Build a downloadable markdown file matching the CLI's report format."""
    sources_md = "\n".join(
        f"[G{s['n']}] [{s['title']}]({s['url']})" for s in result["sources"]
    )
    return (
        f"# Research Report\n\n"
        f"**Query:** {result['query']}\n\n"
        f"**Generated:** {datetime.now().isoformat(timespec='seconds')}  \n"
        f"**Runtime:** {result['elapsed_seconds']:.1f}s  \n"
        f"**Sources:** {len(result['sources'])}\n\n---\n\n"
        f"{result['report']}\n\n---\n\n## Sources\n\n{sources_md}\n"
    )


# ── Header ────────────────────────────────────────────────────────────────
st.title("🔍 Research Assistant")
st.caption(
    "Ask any research question. A team of agents plans the angles, searches the "
    "web in parallel, and synthesizes a cited report."
)

# ── Input ─────────────────────────────────────────────────────────────────
with st.form("research_form"):
    query = st.text_area(
        "Your question",
        placeholder="e.g. How does Anthropic's MCP protocol compare to OpenAI's tools?",
        height=90,
    )
    submitted = st.form_submit_button("Research", type="primary")

# ── Run + render ──────────────────────────────────────────────────────────
if submitted:
    if not query.strip():
        st.warning("Please enter a question first.")
    else:
        with st.status("Researching…", expanded=True) as status:
            st.write("📋 Planning subtasks and searching the web in parallel…")
            try:
                result = run_research_sync(query.strip())
                status.update(
                    label=f"Done in {result['elapsed_seconds']:.1f}s",
                    state="complete",
                    expanded=False,
                )
            except Exception as e:  # surface errors instead of a blank page
                status.update(label="Something went wrong", state="error")
                st.error(f"Research failed: {e}")
                st.stop()

        # Top-line metrics
        c1, c2 = st.columns(2)
        c1.metric("Sources", len(result["sources"]))
        c2.metric("Runtime", f"{result['elapsed_seconds']:.1f}s")

        # The report itself — rendered markdown (headings, citations, etc.)
        st.markdown(result["report"])

        # Sources
        st.subheader("Sources")
        for s in result["sources"]:
            st.markdown(f"**[G{s['n']}]** [{s['title']}]({s['url']})")

        # Research plan (collapsed — for the curious)
        with st.expander("How this was researched"):
            for st_task in result["subtasks"]:
                st.markdown(
                    f"- **{st_task['topic']}** — {st_task.get('rationale', '')}"
                )

        # Download
        st.download_button(
            "⬇️ Download report (Markdown)",
            data=report_to_markdown(result),
            file_name=f"research_{datetime.now():%Y%m%d-%H%M%S}.md",
            mime="text/markdown",
        )
