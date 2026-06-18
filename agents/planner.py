"""Planner agent — decomposes a research query into parallel subtasks."""
from agents.base import Agent
from config import MODEL_PRO


PLANNER_SYSTEM_PROMPT = """You are a research planning agent.

Your job: take a user's research question and break it into exactly 3 focused, NON-OVERLAPPING search subtasks that, when answered together, fully address the question.

Rules:
- Each subtask must be independently researchable via a web search.
- Subtasks must cover DIFFERENT angles (not rephrasings of each other).
- Prefer specificity over breadth. "X's market share in 2025" beats "About X".
- Output ONLY valid JSON. No prose, no markdown fences.

Output schema:
{
  "subtasks": [
    {
      "id": 1,
      "topic": "<short label, 3-6 words>",
      "search_query": "<the actual query to send to a search engine, optimized for retrieval>",
      "rationale": "<one sentence on why this angle matters>"
    }
  ]
}
"""


class Planner(Agent):
    def __init__(self):
        super().__init__(
            name="planner",
            model=MODEL_PRO,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            temperature=0.4,
        )

    async def plan(self, query: str) -> list[dict]:
        """Return list of subtask dicts."""
        result = await self.run(query, expect_json=True)
        subtasks = result.get("subtasks", [])
        if not subtasks:
            raise ValueError(f"Planner returned no subtasks. Raw: {result}")
        return subtasks