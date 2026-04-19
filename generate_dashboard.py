import json
import base64
import urllib.request
import urllib.parse

def generate_dashboard():
    try:
        with open("audit_log.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading audit_log.json: {e}")
        return

    resolved = sum(1 for d in data if d["decision"] == "resolved")
    escalated = sum(1 for d in data if d["decision"] == "escalated")
    dlq = sum(1 for d in data if d["decision"] == "dlq")
    total = len(data)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ShopWave Agent Audit Dashboard</title>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; background: #0d1117; color: #c9d1d9; padding: 2em; }}
        h1 {{ color: #58a6ff; }}
        .metrics {{ display: flex; gap: 20px; }}
        .card {{ background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; flex: 1; text-align: center; }}
        .card h2 {{ font-size: 3em; margin: 0; }}
        .resolved h2 {{ color: #238636; }}
        .escalated h2 {{ color: #d29922; }}
        .dlq h2 {{ color: #da3633; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 2em; }}
        th, td {{ border: 1px solid #30363d; padding: 12px; text-align: left; }}
        th {{ background: #21262d; }}
    </style>
</head>
<body>
    <h1>ShopWave Autonomous Support Agent Metrics</h1>
    <div class="metrics">
        <div class="card resolved">
            <h2>{resolved}</h2>
            <p>Tickets Resolved Autonomously</p>
        </div>
        <div class="card escalated">
            <h2>{escalated}</h2>
            <p>Tickets Escalated Safely</p>
        </div>
        <div class="card dlq">
            <h2>{dlq}</h2>
            <p>Failure Cases Isolated (DLQ)</p>
        </div>
    </div>
    
    <h2>Ticket Audit Log</h2>
    <table>
        <tr>
            <th>Ticket ID</th>
            <th>Decision Finalised</th>
            <th>Reasoning Steps Taken</th>
            <th>Tools Utilised</th>
        </tr>
"""
    for tkt in data:
        tools_list = ", ".join(list(set([a["tool"] for a in tkt.get("audit_trail", [])])))
        html += f"""        <tr>
            <td>{tkt.get('ticket_id')}</td>
            <td>{tkt.get('decision')}</td>
            <td>{tkt.get('iterations')}</td>
            <td>{tools_list}</td>
        </tr>
"""
    
    html += """    </table>
</body>
</html>"""

    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Dashboard generated: dashboard.html")

def generate_architecture_png():
    # Render architecture diagram using Kroki API (Mermaid)
    mermaid_code = '''
    graph TD
    A[Incoming Tickets] --> B[Concurrent Scheduler asyncio]
    B --> C[Agent Orchestrator LangGraph]
    C --> D{Evaluate Decision}
    D -- Need Tools --> E[Tools Node + @chaos_monkey]
    E -- Error / Timeout --> C
    E -- Success --> C
    D -- End loop / DLQ --> F[Audit Log JSON]
    D -- Final Answer --> F
    E -.-> G[TF-IDF Semantic Kernel]
    '''
    
    encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
    url = f"https://kroki.io/mermaid/png/{encoded}"
    try:
        urllib.request.urlretrieve(url, "architecture.png")
        print("Architecture diagram downloaded: architecture.png")
    except Exception as e:
        print(f"Warning: Could not download architecture.png via Kroki. Error: {e}")

if __name__ == "__main__":
    generate_dashboard()
    generate_architecture_png()
