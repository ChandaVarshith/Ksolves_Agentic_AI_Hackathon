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
We have completely engineered a state-of-the-art **Multi-Agent Supervisor Network** using LangGraph to automate the triage pipeline securely.

- **Supervisor Routing**: A central LLM router categorizes tickets by intent, dynamically dispatching them to purely constrained **Refund Sub-Agents** or **Support Policy Sub-Agents** to prevent hallucination boundaries.
- **Self-Reflective Critique Node**: Before any ticket is resolved, a separate isolated `Reviewer` Node evaluates the generated response. If the agent promised a refund without calling the internal tools, the Reviewer intercepts the response and forces a retry, structurally preventing policy violations.
- **Deep Thread Memory (Checkpointers)**: The network uses SQLite-style `MemorySaver` wrappers. In the event of catastrophic `HTTP 500` or `429 Rate Limit` timeouts, the agent falls asleep and resumes perfectly from the exact sub-node it crashed at without wasting tokens or re-running completed queries.
- **Dense Matrix Embeddings**: Utilizing true math vectorization via stable local `TF-IDF` matrices (SciKit-Learn) to capture semantic search context perfectly without breaking lightweight environments.
- **Chaos-Resilient Transactions**: ShopWave’s mock legacy APIs are wrapped in a `@chaos_monkey` interceptor that strictly tests the AI recovery behaviors during API latency drops.

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
