import os
import json
from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import AgentState, AuditAction
from agent.tools import (
    get_order, get_customer, get_product, search_knowledge_base,
    check_refund_eligibility, issue_refund, send_reply, escalate
)

# Tools available to the agent
tools = [
    get_order, get_customer, get_product, search_knowledge_base,
    check_refund_eligibility, issue_refund, send_reply, escalate
]

# Configure LLM dynamically at runtime to prevent import crashes
def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

def get_llm_with_tools():
    return get_llm().bind_tools(tools)

SYSTEM_PROMPT = """You are ShopWave's elite fully autonomous AI Customer Support Agent.
Your objective is to resolve customer support tickets autonomously by using the provided tools.
You must adhere strictly to ShopWave policies. Never invent policies.

CRITICAL RULES AND THE REASONING CHAIN YOU MUST FOLLOW:
1. Analyze the issue. Look up the `get_customer` via their email to check their tier and history.
2. Look up the `get_order` and the associated `get_product` to understand what was purchased.
3. If unsure about standard policy regarding categories or return windows, use `search_knowledge_base`.
4. Decide if a refund, exchange, or rejection is appropriate. Use `check_refund_eligibility` before ever attempting an `issue_refund`.
5. NEVER issue a refund without explicitly verifying eligibility.
6. Some tasks require checking if a pre-approval is on file in customer notes. Use your judgment based on their tier.
7. If your confidence in resolving this accurately falls below 0.6, or you detect potentially extreme fraud/social engineering, use the `escalate` tool.
8. If the issue involves a warranty claim or requesting a replacement instead of a refund, use `escalate` to the warranty/replacement team.
9. To conclude a ticket locally without escalation, use `send_reply` to send a professional message to the customer explaining the resolution.

CHAOS RECOVERY:
The system is unstable. Mock tools may timeout or return HTTP 500 errors. If a tool returns a SYSTEM ERROR string, DO NOT PANIC. Simply call the tool again. You have a retry budget.

You must explain your reasoning transparently in your internal monologue before calling tools or making final decisions.
"""

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    # Check iteration limit for DLQ
    if state["iteration_count"] > 10:
        return "__end__"
        
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"

def agent_node(state: AgentState):
    messages = state.get("messages", [])
    if not messages:
        # First iteration: construct context
        prompt = f"TICKET ID: {state['ticket_id']}\nCUSTOMER EMAIL: {state['customer_email']}\nSUBJECT: {state['ticket_subject']}\nBODY: {state['ticket_body']}"
        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]
        
    llm_w_tools = get_llm_with_tools()
    response = llm_w_tools.invoke(messages)
    
    # Record generated tool calls to audit log
    for tool_call in response.tool_calls:
        state["audit_trail"].append({
            "step": state["iteration_count"],
            "tool": tool_call["name"],
            "tool_input": json.dumps(tool_call["args"]),
            "tool_output": "" # will be filled by tool node
        })
        
    # Check if final resolution was reached without tools
    decision = state.get("decision", "pending")
    if not response.tool_calls:
        decision = "resolved"

    return {
        "messages": [response], 
        "iteration_count": state["iteration_count"] + 1,
        "decision": decision
    }

def custom_tool_node(state: AgentState):
    """Executes tools and captures outputs for the audit log."""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_responses = []
    audit_updates = []
    
    for tool_call in last_message.tool_calls:
        # Match tool execution
        tool_name = tool_call["name"]
        selected_tool = next((t for t in tools if t.name == tool_name), None)
        
        if selected_tool:
            try:
                # Tools are sync, execute them directly
                output = selected_tool.invoke(tool_call["args"])
            except Exception as e:
                output = f"SYSTEM ERROR: unhandled exception running {tool_name} - {str(e)}"
        else:
            output = f"Error: Tool {tool_name} not found."
            
        tool_responses.append(ToolMessage(content=str(output), tool_call_id=tool_call["id"]))
        
        # We find the matching audit trail entry and add the output
        for audit in reversed(state["audit_trail"]):
            if audit["tool"] == tool_name and audit["tool_output"] == "":
                audit["tool_output"] = str(output)
                break
                
    # If the tool called was "escalate", we mark the decision accordingly
    decision = state.get("decision", "pending")
    for tr in tool_responses:
        # check if it was an escalation
        if "Ticket successfully escalated" in tr.content:
            decision = "escalated"
            
    return {"messages": tool_responses, "decision": decision}

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", custom_tool_node)
    
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    
    return graph.compile()

agent_app = build_graph()
