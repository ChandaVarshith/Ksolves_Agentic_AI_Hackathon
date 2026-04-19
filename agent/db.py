import json
import os
from typing import Dict, List, Any

# Mock Datastore

class MockDB:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.customers: Dict[str, Any] = {}
        self.orders: Dict[str, Any] = {}
        self.products: Dict[str, Any] = {}
        self.tickets: List[Any] = []
        
        self.load_data()

    def load_data(self):
        # Load customers
        customers_path = os.path.join(self.data_dir, "customers.json")
        if os.path.exists(customers_path):
            with open(customers_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.customers = {c.get("email"): c for c in data if c.get("email")}
                
        # Load orders
        orders_path = os.path.join(self.data_dir, "orders.json")
        if os.path.exists(orders_path):
            with open(orders_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.orders = {o.get("order_id"): o for o in data if o.get("order_id")}
                
        # Load products
        products_path = os.path.join(self.data_dir, "products.json")
        if os.path.exists(products_path):
            with open(products_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.products = {p.get("product_id"): p for p in data if p.get("product_id")}
                
        # Load tickets (List)
        tickets_path = os.path.join(self.data_dir, "tickets.json")
        if os.path.exists(tickets_path):
            with open(tickets_path, "r", encoding="utf-8") as f:
                self.tickets = json.load(f)

    def get_order(self, order_id: str) -> dict:
        return self.orders.get(order_id)

    def get_customer(self, email: str) -> dict:
        return self.customers.get(email)

    def get_product(self, product_id: str) -> dict:
        return self.products.get(product_id)

    def update_order_refund_status(self, order_id: str, amount: float):
        if order_id in self.orders:
            self.orders[order_id]["refund_status"] = "refunded"
            self.orders[order_id]["refund_amount"] = amount
            return True
        return False

# Global instance
db = MockDB()
