"""Worker agent — runs one search subtask and produces a focused mini-report."""
from agents.base import Agent
from tools.search import web_search, format_results
from config import MODEL_FLASH


WORKER_SYSTEM_PROMPT = """You are a research worker agent.

You are given:
1. A specific subtopic to investigate.
2. A set of web search results (numbered [1], [2], ...).

Your job: extract the key facts, figures, dates, and claims from the results that are RELEVANT to the subtopic. Produce a focused mini-report.

Rules:
- Stick to information actually present in the search results. Do NOT invent facts.
- Cite sources inline using the bracket numbers from the search results, e.g. "ITER first plasma is delayed to 2034 [2]".
- Prefer concrete numbers, dates, and named entities over vague statements.
- If sources conflict, note the disagreement.
- If the results are insufficient, say so explicitly.
- Keep it under 250 words. Dense and factual, no fluff.
- Output plain text. No headers, no markdown formatting beyond inline citation brackets.
"""


class Worker(Agent):
    def __init__(self):
        super().__init__(
            name="worker",
            model=MODEL_FLASH,
            system_prompt=WORKER_SYSTEM_PROMPT,
            temperature=0.2,
        )

    async def execute(self, subtask: dict) -> dict:
        """Run search + extraction for one subtask. Returns dict with findings + sources."""
        topic = subtask["topic"]
        query = subtask["search_query"]

        # 1. Search the web
        results = await web_search(query, max_results=5, search_depth="basic")

        if not results:
            return {
                "id": subtask["id"],
                "topic": topic,
                "findings": "(no search results returned)",
                "sources": [],
            }

        # 2. Feed results to LLM for extraction
        prompt = (
            f"SUBTOPIC: {topic}\n\n"
            f"SEARCH RESULTS:\n{format_results(results)}\n\n"
            f"Write the focused mini-report now."
        )
        findings = await self.run(prompt, expect_json=False)

        return {
            "id": subtask["id"],
            "topic": topic,
            "findings": findings,
            "sources": [
                {"n": i + 1, "title": r["title"], "url": r["url"]}
                for i, r in enumerate(results)
            ],
        }