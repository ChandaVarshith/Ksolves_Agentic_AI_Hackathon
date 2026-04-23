import os
import json
from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState, AuditAction
from agent.tools import (
    get_order, get_customer, get_product, search_knowledge_base,
    check_refund_eligibility, issue_refund, send_reply, escalate
)

# Tool Groups for specializations
db_tools = [get_order, get_customer, get_product, check_refund_eligibility, issue_refund, escalate]
support_tools = [search_knowledge_base, get_customer, get_order, send_reply, escalate]
all_tools = db_tools + support_tools

def get_llm():
    groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    return ChatGroq(
        model="llama-3.1-8b-instant",  
        temperature=0.0,
        api_key=groq_api_key
    )

async def router_node(state: AgentState):
    """SUPERVISOR: Analyzes the initial ticket and routes it to the specialized sub-agent."""
    messages = state.get("messages", [])
    if not messages:
        # Intial setup
        prompt = f"TICKET ID: {state['ticket_id']}\nCUSTOMER EMAIL: {state['customer_email']}\nSUBJECT: {state['ticket_subject']}\nBODY: {state['ticket_body']}"
        state["messages"] = [HumanMessage(content=prompt)]
        
    llm = get_llm()
    # Zero-shot classification routing
    routing_prompt = f"""You are the ShopWave Operations Supervisor. Classify the ticket intent exactly as either 'refund_specialist' or 'support_specialist'.
Ticket Subject: {state['ticket_subject']}
Body: {state['ticket_body']}
Output ONLY the classifying string."""
    
    response = await llm.ainvoke([SystemMessage(content=routing_prompt)])
    decision = response.content.strip().lower()
    
    if "refund" in decision or "database" in decision or "order" in decision:
        return {"decision": "refund_specialist"}
    else:
        return {"decision": "support_specialist"}

async def refund_specialist_node(state: AgentState):
    """SUB-AGENT: Strict database and refund policies."""
    sys_prompt = "You are the Refund Specialist Sub-Agent. Your tools are check_refund_eligibility, issue_refund, get_order, get_product, escalate. Never hallucinate rules. DO NOT attempt to answer general policy questions. ONLY solve refund issues or escalate."
    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    llm = get_llm().bind_tools(db_tools)
    response = await llm.ainvoke(messages)
    
    for t_call in response.tool_calls:
        state["audit_trail"].append({"step": state["iteration_count"], "tool": t_call["name"], "tool_input": str(t_call["args"]), "tool_output": ""})
    return {"messages": [response], "iteration_count": state["iteration_count"]+1}

async def support_specialist_node(state: AgentState):
    """SUB-AGENT: Uses Embeddings and FAQ."""
    sys_prompt = "You are the Support Specialist Sub-Agent. Use search_knowledge_base to answer questions mathematically. Do not attempt direct refund actions. Reply to customer using send_reply."
    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    llm = get_llm().bind_tools(support_tools)
    response = await llm.ainvoke(messages)
    
    for t_call in response.tool_calls:
        state["audit_trail"].append({"step": state["iteration_count"], "tool": t_call["name"], "tool_input": str(t_call["args"]), "tool_output": ""})
    return {"messages": [response], "iteration_count": state["iteration_count"]+1}

async def reviewer_node(state: AgentState):
    """CRITIQUE: Before final conclusion, verifies the LLM's draft."""
    messages = state["messages"]
    last_msg = messages[-1]
    
    # If it's a draft response attempting to finish the flow
    if hasattr(last_msg, "tool_calls") and not last_msg.tool_calls:
        llm = get_llm()
        critique_prompt = f"Verify this response draft: '{last_msg.content}'. If it promises a refund but no refund tools were used, output 'REJECT'. Otherwise output 'APPROVE'."
        critique = await llm.ainvoke([SystemMessage(content=critique_prompt)])
        
        if "REJECT" in critique.content:
            return {"messages": [HumanMessage(content="Reviewer Rejected your draft: Hallucination detected regarding refunds or policy. Please fix and use tools.")], "decision": "escalated"}
            
    return {"decision": "resolved" if (not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls) else "pending"}

async def execute_tool_node(state: AgentState):
    try:
        last_msg = state["messages"][-1]
        responses = []
        for call in last_msg.tool_calls:
            try:
                found_tool = next((t for t in all_tools if t.name == call["name"]), None)
                if not found_tool:
                    out = f"Error: Tool {call['name']} not found."
                else:
                    # Execute async if valid, fallback to sync execution safely using asyncio
                    out = found_tool.invoke(call["args"])
            except Exception as e:
                out = f"SYSTEM ERROR: exception running {call['name']} - {str(e)}"
            
            responses.append(ToolMessage(content=str(out), tool_call_id=call["id"]))
            
            # Map audit trail
            for audit in reversed(state["audit_trail"]):
                if audit["tool"] == call["name"] and audit["tool_output"] == "":
                    audit["tool_output"] = str(out)
                    break
        
        return {"messages": responses}
    except Exception as e:
        print(f"Tool execution graph error: {e}")
        return {"messages": []}

def decide_next(state: AgentState):
    if state["iteration_count"] > 10:
        return "__end__"
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "reviewer"
    
def select_specialist(state: AgentState):
    if state["decision"] == "refund_specialist":
        return "refund"
    return "support"

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("refund", refund_specialist_node)
    graph.add_node("support", support_specialist_node)
    graph.add_node("tools", execute_tool_node)
    graph.add_node("reviewer", reviewer_node)
    
    graph.set_entry_point("router")
    
    graph.add_conditional_edges("router", select_specialist, {"refund": "refund", "support": "support"})
    
    graph.add_conditional_edges("refund", decide_next, {"tools": "tools", "reviewer": "reviewer", "__end__": END})
    graph.add_conditional_edges("support", decide_next, {"tools": "tools", "reviewer": "reviewer", "__end__": END})
    
    # After tools are executed, go back to router to potentially switch specialists if the task is complex
    graph.add_edge("tools", "router")
    graph.add_edge("reviewer", END)
    
    # State-of-the-art Thread Memory persistance
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)

agent_app = build_graph()
