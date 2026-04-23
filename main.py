import asyncio
import json
import os
import random
import os
import colorama
from colorama import Fore, Style
from dotenv import load_dotenv

from agent.db import db
from agent.graph import agent_app

colorama.init(autoreset=True)

async def process_ticket(ticket: dict, sem: asyncio.Semaphore):
    async with sem:
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
    
    max_retries = 15
    for attempt in range(max_retries):
        try:
            final_state = await agent_app.ainvoke(state)
            
            # Check if it hit the dead-letter queue (DLQ) condition
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
            err_msg = str(e)
            if "429" in err_msg or "Rate limit" in err_msg:
                # Groq Free Tier has strict 30 Requests Per Minute (RPM). 
                # It can lock the IP for up to 60 seconds when hitting the roof.
                sleep_time = 35 + (attempt * 15) + random.uniform(0, 5)
                print(f"[{ticket['ticket_id']}] {Fore.YELLOW}Rate limit burst! Waiting {sleep_time:.1f}s for the token bucket to unlock ({attempt+1}/{max_retries})...{Style.RESET_ALL}")
                await asyncio.sleep(sleep_time)
            else:
                print(f"[{ticket['ticket_id']}] {Fore.RED}FATAL ERROR: {err_msg}{Style.RESET_ALL}")
                return {
                    "ticket_id": ticket["ticket_id"],
                    "decision": "dlq",
                    "iterations": -1,
                    "error_msg": err_msg,
                    "audit_trail": state["audit_trail"]
                }
    
    # If exhausted
    print(f"[{ticket['ticket_id']}] {Fore.RED}FATAL ERROR: Max retries exceeded due to rate limits.{Style.RESET_ALL}")
    return {"ticket_id": ticket["ticket_id"], "decision": "dlq", "iterations": -1, "error_msg": "Rate Limit Exceeded", "audit_trail": state["audit_trail"]}

async def main():
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        print(f"{Fore.RED}WARNING: API Key is not set in environment.{Style.RESET_ALL}")
        print("Please set your API key in the .env file (GROQ_API_KEY or OPENAI_API_KEY).")
        return

    print(f"{Fore.GREEN}ShopWave Autonomous Support Agent Initializing...{Style.RESET_ALL}")
    print(f"Loaded {len(db.tickets)} mock tickets.")
    
    if len(db.tickets) == 0:
        print("No tickets found to process. Make sure data/tickets.json exists.")
        return
        
    print("\n--- Processing Tickets Concurrently (Throttled for API Limits) ---\n")
    
    # Use a Semaphore to prevent blasting Groq rate limits all at once
    # This maintains concurrency (running 3 tickets simultaneously) while respecting the 12K TPM limit
    sem = asyncio.Semaphore(3)
    
    # Run all tickets concurrently via asyncio.gather
    tasks = [process_ticket(tkt, sem) for tkt in db.tickets]
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
