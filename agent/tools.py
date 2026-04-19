import functools
import random
import time
import os
import re
from typing import Optional, Dict

from langchain_core.tools import tool
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from agent.db import db

# Chaos Engineering Decorator
def chaos_monkey(func):
    """
    Simulates real-world transient failures for the hackathon requirements.
    - 5% chance of returning a Timeout error message string.
    - 5% chance of HTTP 500 equivalent message string.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        r = random.random()
        if r < 0.05:
            time.sleep(1)
            return f"SYSTEM ERROR: Tool {func.__name__} timed out. Please retry."
        elif r < 0.10:
            return f"SYSTEM ERROR: Tool {func.__name__} encountered an internal server error (HTTP 500). Please retry."
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return f"SYSTEM ERROR: Unhandled exception in {func.__name__}: {str(e)}"
    return wrapper


# 1. Semantic Search Engine for Knowledge Base
class KnowledgeBaseSearcher:
    def __init__(self, kb_path: str = "data/knowledge-base.md"):
        self.sections = []
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Split by headings
            raw_sections = re.split(r'\n(?=\d+\.\s)', content)
            self.sections = [s.strip() for s in raw_sections if s.strip()]
        
        if self.sections:
            self.vectorizer = TfidfVectorizer(stop_words='english')
            self.tfidf_matrix = self.vectorizer.fit_transform(self.sections)
        else:
            self.vectorizer = None

    def search(self, query: str, top_k: int = 2) -> str:
        if not self.vectorizer:
            return "Knowledge base not loaded."
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.05: # Minimum threshold
                results.append(self.sections[idx])
                
        if not results:
            return "No relevant policies found in the knowledge base."
        return "\n\n---\n\n".join(results)

kb_searcher = KnowledgeBaseSearcher()

# Tools definitions
@tool
@chaos_monkey
def get_order(order_id: str) -> str:
    """Retrieve details for a given order ID. Use this to find out what product was ordered and the delivery status/dates."""
    order = db.get_order(order_id)
    if not order:
        return f"Error: Order {order_id} not found."
    return str(order)

@tool
@chaos_monkey
def get_customer(email: str) -> str:
    """Retrieve customer profile, including their tier (standard, premium, vip) and history."""
    customer = db.get_customer(email)
    if not customer:
        return f"Error: Customer with email {email} not found."
    return str(customer)

@tool
@chaos_monkey
def get_product(product_id: str) -> str:
    """Retrieve product metadata, warranty months, and return window days."""
    product = db.get_product(product_id)
    if not product:
        return f"Error: Product {product_id} not found."
    return str(product)

@tool
def search_knowledge_base(query: str) -> str:
    """Search the ShopWave knowledge base for policies on returns, refunds, warranty, exchanges, or customer tiers."""
    return kb_searcher.search(query)

@tool
@chaos_monkey
def check_refund_eligibility(order_id: str) -> str:
    """Checks if an order is eligible for a refund purely based on standard dates. Note that VIP or edge cases may require human judgment overriding this."""
    order = db.get_order(order_id)
    if not order:
        return "Error: Order not found."
    if order.get("refund_status") == "refunded":
        return "Not eligible: Order is already refunded."
    
    # We use a mocked concept of 'today' as '2024-03-20' given the dataset dates.
    # We will do simple string comparison for dates YYYY-MM-DD.
    mock_today = "2024-03-20"
    deadline = order.get("return_deadline")
    if deadline and deadline < mock_today:
        return f"Not eligible: Return deadline ({deadline}) has passed as of {mock_today}."
    
    return "Eligible: Order is within the return window."

@tool
def issue_refund(order_id: str, amount: float) -> str:
    """Irreversible action to issue a refund. Ensure eligibility first! Must supply the exact amount."""
    # To keep things robust, we don't chaos monkey this critical write mock directly, but the agent must get here.
    success = db.update_order_refund_status(order_id, amount)
    if success:
        return f"Success: Refund of ${amount} issued for {order_id}."
    return f"Failed: Could not process refund for {order_id}."

@tool
def send_reply(message: str) -> str:
    """Action to resolve the ticket by sending a final resolution message to the customer."""
    return f"Reply sent successfully: {message}"

@tool
def escalate(summary: str, priority: str) -> str:
    """Action to escalate the ticket to a human agent. Use this when uncertain, when confidence < 0.6, or for warranty claims."""
    assert priority in ["low", "medium", "high", "urgent"], "Priority must be low, medium, high, or urgent."
    return f"Ticket successfully escalated to human agents. Priority: {priority}. Summary: {summary}"
