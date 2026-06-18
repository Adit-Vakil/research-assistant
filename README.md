# Research Assistant

A multi-agent research assistant that takes a question, researches it across the
web, and produces a structured, cited report — available both as a command-line
tool and as a browser app.

It uses a three-stage agent pipeline:

1. **Planner** — breaks the question into focused, non-overlapping subtopics.
2. **Workers** — run web searches for each subtopic (in parallel) and extract the
   key facts with inline citations.
3. **Synthesizer** — merges the findings into a single coherent report with a
   unified, deduplicated source list.

## Features

- 🔍 Ask any research question and get a readable, cited report
- 🧩 Multi-agent pipeline (plan → search → synthesize)
- 🌐 Web UI (Streamlit) with live progress, rendered report, clickable sources,
  and Markdown download
- 💻 CLI for quick one-off runs (saves reports to `reports/`)
- ♻️ Resilient API calls — automatic retry/backoff on transient rate-limit and
  server errors

## Requirements

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey)
- A [Tavily API key](https://tavily.com) (for web search)

## Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/Adit-Vakil/research-assistant.git
cd research-assistant

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Add your API keys to a .env file (this file is gitignored)
cat > .env <<'EOF'
GEMINI_API_KEY=your_gemini_key_here
TAVILY_API_KEY=your_tavily_key_here
EOF
```

## Usage

### Web app

```bash
streamlit run app.py
```

Then open the URL it prints (default http://localhost:8501), type a question, and
click **Research**.

### Command line

```bash
# Pass the question as an argument...
python main.py "How does Anthropic's MCP protocol compare to OpenAI's tools?"

# ...or run with no arguments to be prompted interactively
python main.py
```

CLI runs save a Markdown report to the `reports/` folder.

## Project structure

```
app.py            # Streamlit web UI
main.py           # CLI entry point
orchestrator.py   # Runs the planner -> workers -> synthesizer pipeline
config.py         # Loads API keys and model names from .env
agents/
  base.py         # Shared Gemini wrapper with retry/backoff
  planner.py      # Decomposes the question into subtasks
  worker.py       # Searches + extracts findings for one subtask
  synthesizer.py  # Merges findings into the final report
tools/
  search.py       # Tavily web-search helper
reports/          # Saved reports from CLI runs
```

## Configuration

Models are set in `config.py`:

- `MODEL_PRO` — used by the planner and synthesizer
- `MODEL_FLASH` — used by the workers

Note: the free tier of the Gemini API has daily request limits. A single research
run makes several calls, so heavy testing can exhaust the free quota — enable
billing on your key for sustained use.
