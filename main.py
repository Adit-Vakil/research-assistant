"""CLI entry point for the multi-agent research assistant."""
import asyncio
import sys
import re
from datetime import datetime
from pathlib import Path
from orchestrator import run_research


def slugify(text: str, max_len: int = 50) -> str:
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    s = re.sub(r"\s+", "-", s)
    return s[:max_len] or "report"


def save_report(result: dict) -> Path:
    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(result["query"])
    path = out_dir / f"{timestamp}_{slug}.md"

    sources_md = "\n".join(
        f"[G{s['n']}] [{s['title']}]({s['url']})" for s in result["sources"]
    )

    content = (
        f"# Research Report\n\n"
        f"**Query:** {result['query']}\n\n"
        f"**Generated:** {datetime.now().isoformat(timespec='seconds')}  \n"
        f"**Runtime:** {result['elapsed_seconds']:.1f}s  \n"
        f"**Sources:** {len(result['sources'])}\n\n"
        f"---\n\n"
        f"{result['report']}\n\n"
        f"---\n\n"
        f"## Sources\n\n"
        f"{sources_md}\n"
    )

    path.write_text(content, encoding="utf-8")
    return path


async def main():
    # Allow query via CLI args, else prompt interactively
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Research question: ").strip()

    if not query:
        print("No query provided. Exiting.")
        return

    result = await run_research(query)

    print("=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(result["report"])
    print()

    path = save_report(result)
    print(f"✅ Saved to: {path}")


if __name__ == "__main__":
    asyncio.run(main())
    