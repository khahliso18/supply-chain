import streamlit as st
import hashlib
import json
import time
from typing import List, Dict, Any
import pandas as pd

# -----------------------
# Blockchain Class
# -----------------------
class SupplyChainBlockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.product_counter = 0
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        block_transactions = [tx.copy() for tx in self.pending_transactions]
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": block_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_transactions = []
        block["hash"] = self.hash(block)
        self.chain.append(block)
        return block

    def add_transaction(self, product_id: int, actor: str, location: str, action: str, amount: float) -> int:
        transaction = {
            "product_id": product_id,
            "actor": actor,
            "location": location,
            "action": action,
            "amount": amount,
            "timestamp": time.time()
        }
        self.pending_transactions.append(transaction)
        return product_id

    def create_product(self) -> int:
        self.product_counter += 1
        return self.product_counter

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_copy = block.copy()
        block_copy.pop("hash", None)
        block_string = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr["previous_hash"] != prev["hash"]:
                return False
            if curr["hash"] != self.hash(curr):
                return False
        return True

    def track_product(self, product_id: int) -> List[Dict[str, Any]]:
        history = []
        for block in self.chain:
            for tx in block["transactions"]:
                if tx["product_id"] == product_id:
                    history.append({
                        "actor": tx["actor"],
                        "location": tx["location"],
                        "action": tx["action"],
                        "amount": tx["amount"],
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tx["timestamp"])),
                        "block_index": block["index"]
                    })
        return history

    def all_transactions_summary(self) -> pd.DataFrame:
        rows = []
        for block in self.chain:
            for tx in block["transactions"]:
                rows.append({
                    "Product ID": tx["product_id"],
                    "Actor": tx["actor"],
                    "Action": tx["action"],
                    "Location": tx["location"],
                    "Amount": tx["amount"],
                    "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tx["timestamp"])),
                    "Block": block["index"]
                })
        return pd.DataFrame(rows)

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="🚚 Supply Chain Tracker", layout="wide")

# Initialize blockchain
if "supply_chain" not in st.session_state:
    st.session_state.supply_chain = SupplyChainBlockchain()

bc: SupplyChainBlockchain = st.session_state.supply_chain

# Sidebar navigation
st.sidebar.title("🚚 Supply Chain Navigation")
menu = st.sidebar.radio("Navigate", ["🏠 Home", "🆕 Register Product", "📦 Add Step", "🔍 Track Product", "📊 Ledger"])

# --- Home / Dashboard ---
if menu == "🏠 Home":
    st.title("🚚 Blockchain Supply Chain Tracker")
    st.subheader("📊 Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Products", bc.product_counter)
    total_steps = sum(len(block["transactions"]) for block in bc.chain)
    col2.metric("Total Steps Recorded", total_steps)
    col3.metric("Chain Validity", "✅ Yes" if bc.is_chain_valid() else "❌ No")
    
    st.markdown("### 🔹 Recent Steps")
    all_tx = bc.all_transactions_summary()
    if not all_tx.empty:
        st.dataframe(all_tx.tail(10))
    else:
        st.info("No transactions yet.")

# --- Register Product ---
elif menu == "🆕 Register Product":
    st.header("🆕 Register New Product")
    if st.button("Create Product"):
        product_id = bc.create_product()
        st.success(f"✅ Product #{product_id} registered!")

# --- Add Supply Chain Step ---
elif menu == "📦 Add Step":
    st.header("📦 Add Supply Chain Step")
    with st.form("supply_form", clear_on_submit=True):
        product_id = st.number_input("Product ID", min_value=1, step=1)
        actor = st.selectbox("Actor", ["Farmer", "Wholesaler", "Distributor", "Retailer", "Customer"])
        location = st.text_input("Location")
        action = st.text_input("Action/Status (e.g., 'Harvested', 'Shipped', 'Delivered')")
        amount = st.number_input("Amount/Quantity", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("Add Step")
        if submitted and actor and location and action:
            bc.add_transaction(product_id, actor, location, action, amount)
            block = bc.new_block(proof=123)
            st.success(f"✅ Step added for Product #{product_id} in Block {block['index']}.")

# --- Track Product ---
elif menu == "🔍 Track Product":
    st.header("🔍 Track Product")
    track_id = st.number_input("Enter Product ID to Track", min_value=1, step=1)
    if st.button("Track Product"):
        history = bc.track_product(track_id)
        if history:
            st.success(f"📜 Product #{track_id} Supply Chain History:")
            st.dataframe(pd.DataFrame(history)[["block_index", "actor", "action", "location", "amount", "timestamp"]].rename(
                columns={"block_index": "Block", "actor": "Actor", "action": "Action", "location": "Location", "amount": "Amount", "timestamp": "Timestamp"}
            ))
        else:
            st.error(f"❌ No record found for Product #{track_id}")

# --- Ledger / Explorer ---
elif menu == "📊 Ledger":
    st.header("📊 Blockchain Ledger Explorer")
    for block in reversed(bc.chain):
        with st.expander(f"Block {block['index']} (Hash: {block['hash'][:12]}...)"):
            st.write("Previous Hash:", block.get("previous_hash"))
            st.write("Hash:", block.get("hash"))
            st.json(block.get("transactions", []))
