import asyncio
import json
import os
import colorama
from colorama import Fore, Style
from dotenv import load_dotenv

from agent.db import db
from agent.graph import agent_app

colorama.init(autoreset=True)

async def process_ticket(ticket: dict):
    print(f"[{ticket['ticket_id']}] {Fore.CYAN}Starting processing...{Style.RESET_ALL}")
    
    # Initialize state
    state = {
        "ticket_id": ticket["ticket_id"],
        "ticket_subject": ticket["subject"],
        "ticket_body": ticket["body"],
        "customer_email": ticket["customer_email"],
        "messages": [],
        "confidence_score": 1.0,
        "sentiment": "neutral",
        "decision": "pending",
        "audit_trail": [],
        "iteration_count": 0
    }
    
    try:
        final_state = await agent_app.ainvoke(state)
        
        # Check if it hit the dead-letter queue (DLQ) condition (iteration_count > 10)
        decision = final_state.get("decision")
        if final_state.get("iteration_count", 0) > 10:
            decision = "dlq"
        
        # Compile summary
        result = {
            "ticket_id": ticket["ticket_id"],
            "decision": decision,
            "iterations": final_state.get("iteration_count"),
            "audit_trail": final_state.get("audit_trail", [])
        }
        
        color = Fore.GREEN if decision == "resolved" else (Fore.YELLOW if decision == "escalated" else Fore.RED)
        print(f"[{ticket['ticket_id']}] {color}Completed with decision: {decision}{Style.RESET_ALL}")
        return result
        
    except Exception as e:
        print(f"[{ticket['ticket_id']}] {Fore.RED}FATAL ERROR: {str(e)}{Style.RESET_ALL}")
        return {
            "ticket_id": ticket["ticket_id"],
            "decision": "dlq",
            "iterations": -1,
            "error_msg": str(e),
            "audit_trail": state["audit_trail"]
        }

async def main():
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print(f"{Fore.RED}WARNING: OPENAI_API_KEY is not set in environment.{Style.RESET_ALL}")
        print("Please set your API key in the .env file.")
        return

    print(f"{Fore.GREEN}ShopWave Autonomous Support Agent Initializing...{Style.RESET_ALL}")
    print(f"Loaded {len(db.tickets)} mock tickets.")
    
    if len(db.tickets) == 0:
        print("No tickets found to process. Make sure data/tickets.json exists.")
        return
        
    print("\n--- Processing Tickets Concurrently ---\n")
    
    # Run all tickets concurrently via asyncio.gather
    tasks = [process_ticket(tkt) for tkt in db.tickets]
    results = await asyncio.gather(*tasks)
    
    # Save the output to audit_log.json
    with open("audit_log.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    # Calculate simple stats
    resolved = sum(1 for r in results if r["decision"] == "resolved")
    escalated = sum(1 for r in results if r["decision"] == "escalated")
    dlq = sum(1 for r in results if r["decision"] == "dlq")
    
    print("\n--- FINAL METRICS ---")
    print(f"Total Tickets Processed : {len(results)}")
    print(f"Resolved Autonomously   : {Fore.GREEN}{resolved}{Style.RESET_ALL}")
    print(f"Escalated to Human      : {Fore.YELLOW}{escalated}{Style.RESET_ALL}")
    print(f"Dead-Letter Queue (DLQ) : {Fore.RED}{dlq}{Style.RESET_ALL}")
    print("\nWritten detailed execution trace to `audit_log.json`.")

if __name__ == "__main__":
    asyncio.run(main())
