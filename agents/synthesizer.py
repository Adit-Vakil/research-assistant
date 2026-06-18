"""Synthesizer agent — merges worker findings into a final research report."""
from agents.base import Agent
from config import MODEL_PRO


SYNTHESIZER_SYSTEM_PROMPT = """You are a research synthesis agent.

You are given:
1. The user's original research question.
2. Several mini-reports from worker agents, each covering a different subtopic.
   Each mini-report has its own local citation numbers like [1], [2] that refer to ITS OWN source list.
3. A unified source list where each source has a GLOBAL number, e.g. [G3], [G7].

Your job: produce a single, well-structured final research report that directly answers the user's question.

Rules:
- Write a coherent narrative, not a list of disconnected facts.
- Synthesize ACROSS subtopics — connect findings, note tensions, draw conclusions.
- Use ONLY the GLOBAL citation numbers (e.g. [G3], [G7]) in your output. Never use the local [1], [2] numbers from the mini-reports.
- Every concrete claim, number, or date must have at least one global citation.
- Structure: open with a 2-3 sentence direct answer to the question, then sections covering the major angles, then a short "Bottom line" paragraph.
- Use markdown headings (## Section Name) for structure.
- 500-800 words. Dense, no filler, no hedging language like "it's important to note".
- Do NOT include a source list at the end — that will be appended separately.
"""


def _build_global_sources(findings: list[dict]) -> tuple[list[dict], dict]:
    """Deduplicate sources by URL, assign global numbers, build local->global map."""
    global_sources: list[dict] = []
    url_to_global: dict[str, int] = {}
    # local_map[worker_id][local_n] -> global_n
    local_map: dict[int, dict[int, int]] = {}

    for f in findings:
        local_map[f["id"]] = {}
        for src in f["sources"]:
            url = src["url"]
            if url not in url_to_global:
                global_n = len(global_sources) + 1
                url_to_global[url] = global_n
                global_sources.append({"n": global_n, "title": src["title"], "url": url})
            local_map[f["id"]][src["n"]] = url_to_global[url]

    return global_sources, local_map


def _remap_citations(findings: list[dict], local_map: dict) -> str:
    """Build a single prompt string with all findings, citations remapped to global."""
    import re
    blocks = []
    for f in findings:
        text = f["findings"]
        worker_map = local_map[f["id"]]

        # Replace [N] or [N, M, ...] with global [GN], [GN, GM, ...]
        def repl(match):
            nums = [int(x.strip()) for x in match.group(1).split(",")]
            globals_ = [f"G{worker_map.get(n, n)}" for n in nums]
            return "[" + ", ".join(globals_) + "]"

        remapped = re.sub(r"\[(\d+(?:\s*,\s*\d+)*)\]", repl, text)
        blocks.append(f"### Subtopic: {f['topic']}\n{remapped}")

    return "\n\n".join(blocks)


class Synthesizer(Agent):
    def __init__(self):
        super().__init__(
            name="synthesizer",
            model=MODEL_PRO,
            system_prompt=SYNTHESIZER_SYSTEM_PROMPT,
            temperature=0.4,
        )

    async def synthesize(self, query: str, findings: list[dict]) -> dict:
        """Merge findings into a final report. Returns dict with report + sources."""
        global_sources, local_map = _build_global_sources(findings)
        remapped_findings = _remap_citations(findings, local_map)

        sources_block = "\n".join(
            f"[G{s['n']}] {s['title']} — {s['url']}" for s in global_sources
        )

        prompt = (
            f"USER QUESTION:\n{query}\n\n"
            f"WORKER FINDINGS (citations already remapped to global numbers):\n"
            f"{remapped_findings}\n\n"
            f"GLOBAL SOURCE LIST:\n{sources_block}\n\n"
            f"Write the final report now."
        )

        report = await self.run(prompt, expect_json=False)
        return {"report": report, "sources": global_sources}