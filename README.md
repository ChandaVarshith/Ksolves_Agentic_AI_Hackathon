# ShopWave Support Resolution Agent

An extraordinary, fully autonomous support agent powered by LangGraph, LangChain, and structured LLM tool orchestration. This system concurrently processes customer service tickets, intelligently handles chaotic system failures using internal "Chaos Engineering" decorators, and semantic-searches support protocols through a TF-IDF vector heuristic.

**Features Unique to this Hackathon Implementations:**
- **Chaos Validation:** Hardened against intermittent system failures.
- **Dead-Letter Queue:** Automatically parks chronically failing tickets away instead of crashing the batch.
## Problem Statement
ShopWave's customer service team is overwhelmed by repetitive tasks such as looking up order statuses, tracking return deadlines, issuing eligible refunds, and escalating complex queries. The current manual process leads to high resolution times and a poor customer experience. 

The goal of this project is to build an autonomous Agentic AI capable of:
1. Understanding and parsing incoming customer support tickets.
2. Interacting securely with ShopWave's proprietary systems (Order Database, Customer Profiles, Knowledge Base).
3. Making intelligent, policy-compliant decisions on returning products or granting refunds.
4. Knowing when a situation is too ambiguous and effectively escalating it to a human supervisor instead of hallucinating.

## Our Solution Architecture
We have engineered an advanced, robust **ReAct-based LangGraph Pipeline** tailored precisely to automate the ticket triage pipeline while operating safely within unpredictable system parameters.

- **Asynchronous Concurrent Pipeline**: Ingests and processes large batches of internal tickets simultaneously, heavily driving down resolution overhead times.
- **Chaos-Resilient DB Transactions**: ShopWave’s legacy APIs can sometimes timeout or return 500 Network errors. We implemented a `@chaos_monkey` logic layer that mimics these issues. Our LangGraph engine elegantly calculates retry budgets and safely navigates intermittent failures without unhandled exception crashes.
- **Dead-Letter Queue (DLQ) Safeguards**: If a ticket becomes fundamentally unsolvable due to lack of policy data or infinite loop generation, the ticket is parked cleanly in the isolated DLQ, preventing batch lockups.
- **TF-IDF Semantic RAG**: Replaces fragile keyword lookup functions with a Math-backed vector retrieval system, guaranteeing accurate ShopWave policy matching against user queries.
- **Automated Metric Dashboards**: Every action the agent takes is natively appended into an `audit_log.json` object. Our custom parser (`generate_dashboard.py`) transforms this log into a readable managerial dashboard view, exposing cost-savings and AI success rates rapidly.

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
