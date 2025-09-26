import streamlit as st
import hashlib
import json
import time
from typing import List, Dict, Any

# -----------------------
# Blockchain Class
# -----------------------
class SupplyChainBlockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.product_counter = 0
        # Genesis block
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

    def add_transaction(self, product_id: int, actor: str, location: str, action: str) -> int:
        """Add a supply chain step as a transaction"""
        transaction = {
            "product_id": product_id,
            "actor": actor,
            "location": location,
            "action": action,
            "timestamp": time.time()
        }
        self.pending_transactions.append(transaction)
        return product_id

    def create_product(self) -> int:
        """Register a new product in the supply chain"""
        self.product_counter += 1
        product_id = self.product_counter
        return product_id

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
        """Return full supply chain history of a product"""
        history = []
        for block in self.chain:
            for tx in block["transactions"]:
                if tx["product_id"] == product_id:
                    history.append({
                        "actor": tx["actor"],
                        "location": tx["location"],
                        "action": tx["action"],
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tx["timestamp"])),
                        "block_index": block["index"]
                    })
        return history


# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="🚚 Blockchain Supply Chain Tracker", layout="wide")

# Initialize blockchain
if "supply_chain" not in st.session_state:
    st.session_state.supply_chain = SupplyChainBlockchain()

bc: SupplyChainBlockchain = st.session_state.supply_chain

st.title("🚚 Blockchain-based Supply Chain Tracker")

# Chain status
col1, col2 = st.columns(2)
col1.metric("Chain Length", len(bc.chain))
col2.metric("Is Chain Valid?", "✅ Yes" if bc.is_chain_valid() else "❌ No")

# --- Register Product ---
st.header("🆕 Register New Product")
if st.button("Create Product"):
    product_id = bc.create_product()
    st.success(f"✅ Product #{product_id} registered!")

# --- Add Supply Chain Step ---
st.header("📦 Add Supply Chain Step")
with st.form("supply_form", clear_on_submit=True):
    product_id = st.number_input("Product ID", min_value=1, step=1)
    actor = st.selectbox("Actor", ["Farmer", "Wholesaler", "Distributor", "Retailer", "Customer"])
    location = st.text_input("Location")
    action = st.text_input("Action/Status (e.g., 'Harvested', 'Shipped', 'Delivered')")
    submitted = st.form_submit_button("Add Step")
    if submitted and actor and location and action:
        bc.add_transaction(product_id, actor, location, action)
        block = bc.new_block(proof=123)
        st.success(f"✅ Step added for Product #{product_id} in Block {block['index']}.")

# --- Track Product ---
st.header("🔍 Track Product")
track_id = st.number_input("Enter Product ID to Track", min_value=1, step=1, key="track")
if st.button("Track Product", key="track_btn"):
    history = bc.track_product(track_id)
    if history:
        st.success(f"📜 Product #{track_id} Supply Chain History:")
        for step in history:
            st.write(f"- Block {step['block_index']}: {step['actor']} | {step['action']} | {step['location']} | {step['timestamp']}")
    else:
        st.error(f"❌ No record found for Product #{track_id}")

# --- Blockchain Explorer ---
st.header("📊 Blockchain Explorer")
for block in reversed(bc.chain):
    with st.expander(f"Block {block['index']} (Hash: {block['hash'][:12]}...)"):
        st.write("Previous Hash:", block.get("previous_hash"))
        st.write("Hash:", block.get("hash"))
        st.json(block.get("transactions", []))
