import operator
from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage

class AuditAction(TypedDict):
    step: int
    tool: str
    tool_input: str
    tool_output: str

class AgentState(TypedDict):
    ticket_id: str
    ticket_subject: str
    ticket_body: str
    customer_email: str
    
    # LangGraph message history
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Tracking variables requested by metrics
    confidence_score: float
    sentiment: str
    decision: str  # "resolved", "escalated", "dlq"
    
    # Full audit trail for the JSON log
    audit_trail: List[AuditAction]
    
    # Count of loop iterations (to prevent infinite loops)
    iteration_count: int
