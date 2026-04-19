# Failure Mode Analysis

The ShopWave Support Resolution Agent has been explicitly architected to overcome unstable production environments. Below are three primary failure behaviors that our ReAct core successfully mitigates.

## 1. Transient Network/API Timeouts (`TimeoutError`)
**Scenario:** The agent requests data via `get_customer(email)` but the downstream CRM is bottlenecked, causing the tool to fail or stall.
**System Response:** Instead of propagating an uncaught Python exception that crashes the batch execution, the `@chaos_monkey` decorator catches the fault and returns a specific string: `"SYSTEM ERROR: Tool get_customer timed out. Please retry."`
The LangGraph Tool Node relays this exact string back to the LLM context. The system is prompted (`SYSTEM_PROMPT`) to "not panic" and recognize this as a transient failure, safely attempting a retry without abandoning the ticket.

## 2. Unrecoverable Infinite Loops (The DLQ Safeguard)
**Scenario:** A tool chronically returns `HTTP 500` or the LLM hallucinates, locking the agent into repetitive failed execution paths.
**System Response:** LangGraph explicitly intercepts excessive loop behavior. In `agent/graph.py`, the `should_continue` conditional router checks the running state's `iteration_count`. If iterations exceed 10, the loop is forcibly terminated and the ticket's final decision is routed to `dlq` (Dead-Letter Queue). This isolates catastrophic failures away from the main process thread, ensuring system-wide stability.

## 3. Ambiguous Human Escalation Fallback
**Scenario:** The agent queries `search_knowledge_base` using semantic search but gets 0 matches, or identifies an ambiguous refund policy conflict for a high-value customer.
**System Response:** The prompt guarantees that if the LLM's calculated confidence score falls below `0.6` or if the user is threatening/legally ambiguous, it defaults to executing the `escalate` tool rather than hallucinating an action. The system outputs a structured summary to the support staff highlighting exactly what steps it took before it failed context.
