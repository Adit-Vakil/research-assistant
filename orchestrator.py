"""Orchestrator — runs the full planner -> workers -> synthesizer pipeline."""
import asyncio
import time
from agents.planner import Planner
from agents.worker import Worker
from agents.synthesizer import Synthesizer


async def run_research(query: str, verbose: bool = True) -> dict:
    """Execute the full multi-agent research pipeline. Returns dict with report + metadata."""
    t0 = time.time()

    planner = Planner()
    worker = Worker()
    synthesizer = Synthesizer()

    if verbose:
        print(f"🔍 Query: {query}\n")
        print("📋 [1/3] Planning subtasks...")

    subtasks = await planner.plan(query)

    if verbose:
        print(f"   → {len(subtasks)} subtasks:")
        for st in subtasks:
            print(f"      • {st['topic']}")
        print(f"\n⚡ [2/3] Running {len(subtasks)} workers in parallel...")

    t_workers = time.time()
    # Throttle concurrency so we don't fire all workers at once and trip the
    # per-minute rate limit. 2 in flight at a time keeps it fast but gentle.
    sem = asyncio.Semaphore(2)

    async def run_worker(st):
        async with sem:
            return await worker.execute(st)

    findings = await asyncio.gather(*[run_worker(st) for st in subtasks])

    if verbose:
        print(f"   → done in {time.time() - t_workers:.1f}s")
        total_sources = sum(len(f["sources"]) for f in findings)
        print(f"   → {total_sources} sources gathered\n")
        print("🧩 [3/3] Synthesizing final report...")

    result = await synthesizer.synthesize(query, findings)
    elapsed = time.time() - t0

    if verbose:
        print(f"   → done in {elapsed:.1f}s total\n")

    return {
        "query": query,
        "subtasks": subtasks,
        "findings": findings,
        "report": result["report"],
        "sources": result["sources"],
        "elapsed_seconds": elapsed,
    }