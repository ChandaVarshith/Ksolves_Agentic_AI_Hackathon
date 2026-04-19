# ShopWave Support Resolution Agent

An extraordinary, fully autonomous support agent powered by LangGraph, LangChain, and structured LLM tool orchestration. This system concurrently processes customer service tickets, intelligently handles chaotic system failures using internal "Chaos Engineering" decorators, and semantic-searches support protocols through a TF-IDF vector heuristic.

**Features Unique to this Hackathon Implementations:**
- **Chaos Validation:** Hardened against intermittent system failures.
- **Dead-Letter Queue:** Automatically parks chronically failing tickets away instead of crashing the batch.
- **HTML Dashboard Generation:** Exports beautiful management-level visual metrics. 
- **Semantic Matrix Search:** Employs math-backed cosine similarity matching to answer policy questions exactly as requested, escaping hardcoded mappings.

## Quickstart

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure API Key**
Rename `.env.example` to `.env` and assign your `OPENAI_API_KEY` (or compatible LiteLLM key proxy).
```bash
cp .env.example .env
```

3. **Execute the Agent System**
This will concurrently ingest all 20 tickets, simulate realistic timeouts, allow the AI to safely recover and escalate according to policies, and deposit findings into the audit log.
```bash
python main.py
```

4. **Construct Visual Analytics & Architecture Diagrams**
```bash
python generate_dashboard.py
```
This generates the required `architecture.png` and a custom `dashboard.html`.

## System Documentation
Ensure you read `failure_modes.md` for our three specific tested system anomaly events and AI recovery structures.
