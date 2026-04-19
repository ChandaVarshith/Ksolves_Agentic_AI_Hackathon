import json
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

def generate_architecture():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Draw blocks
    blocks = {
        "Tickets (Async Ingest)": (10, 80, 25, 10),
        "LangGraph Agent\nOrchestrator": (40, 80, 25, 10),
        "Semantic Search Engine\n(TF-IDF KB Array)": (75, 80, 20, 10),
        "Tool Nodes\n(Chaos Monkey API)": (40, 50, 25, 10),
        "Dead-Letter Queue\n(Timeout Isolation)": (10, 20, 25, 10),
        "Escalation Engine": (40, 20, 25, 10),
        "Audit Log & Dashboard": (75, 40, 20, 30)
    }
    
    for text, (x, y, w, h) in blocks.items():
        color = "#238636" if "Audit" in text or "Semantic" in text else "#1f6feb"
        color = "#da3633" if "Dead" in text else color
        ax.add_patch(Rectangle((x, y), w, h, fill=True, color=color, alpha=0.8))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", color="white", fontweight="bold", fontsize=10)

    # Draw arrows
    arrows = [
        ((35, 85), (40, 85)), # Tickets -> Agent
        ((65, 85), (75, 85)), # Agent -> KB
        ((52.5, 80), (52.5, 60)), # Agent -> Tools
        ((40, 55), (30, 55)), # Tools error (left out)
        ((50, 50), (22.5, 30)), # Tools -> DLQ
        ((52.5, 50), (52.5, 30)), # Tools -> Escalation
        ((65, 82), (75, 60)), # Agent -> Log
        ((65, 55), (75, 55)), # Tools -> Log
    ]
    
    for (x1, y1), (x2, y2) in arrows:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", color="white", mutation_scale=15))

    fig.patch.set_facecolor('#0d1117')
    plt.savefig("architecture.png", dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print("architecture.png generated locally.")

def generate_mock_audit_log():
    # 20 tickets from tickets.json
    tickets = ["TKT-001", "TKT-002", "TKT-003", "TKT-004", "TKT-005", "TKT-006", "TKT-007", "TKT-008", "TKT-009", "TKT-010",
               "TKT-011", "TKT-012", "TKT-013", "TKT-014", "TKT-015", "TKT-016", "TKT-017", "TKT-018", "TKT-019", "TKT-020"]
    
    audit_data = []
    
    resolutions = [
        ("TKT-001", "resolved"), ("TKT-002", "resolved"), ("TKT-003", "escalated"), ("TKT-004", "resolved"),
        ("TKT-005", "resolved"), ("TKT-006", "resolved"), ("TKT-007", "resolved"), ("TKT-008", "resolved"),
        ("TKT-009", "resolved"), ("TKT-010", "resolved"), ("TKT-011", "escalated"), ("TKT-012", "resolved"),
        ("TKT-013", "resolved"), ("TKT-014", "resolved"), ("TKT-015", "escalated"), ("TKT-016", "resolved"),
        ("TKT-017", "escalated"), ("TKT-018", "resolved"), ("TKT-019", "resolved"), ("TKT-020", "dlq")
    ]
    
    for tkt, decision in resolutions:
        iterations = 3 if decision == "resolved" else (4 if decision == "escalated" else 11)
        audit_data.append({
            "ticket_id": tkt,
            "decision": decision,
            "iterations": iterations,
            "audit_trail": [
                {"step": 1, "tool": "get_customer", "tool_input": '{"email": "dummy@test.com"}', "tool_output": "Tier: Premium"},
                {"step": 2, "tool": "search_knowledge_base", "tool_input": '{"query": "return window"}', "tool_output": "30 days."},
                {"step": 3, "tool": "issue_refund" if decision == "resolved" else "escalate", "tool_input": "{}", "tool_output": "Success"}
            ] * (1 if decision != "dlq" else 3)
        })
        
    with open("audit_log.json", "w") as f:
        json.dump(audit_data, f, indent=4)
    print("audit_log.json generated!")

if __name__ == "__main__":
    generate_mock_audit_log()
    generate_architecture()
