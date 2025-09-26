import streamlit as st
import hashlib
import json
import time
from typing import List, Dict, Any
import qrcode
from io import BytesIO

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def _init_(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
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

    def new_ticket(self, organizer: str, event: str, ticket_id: str, buyer: str):
        tx = {
            "organizer": organizer,
            "event": event,
            "ticket_id": ticket_id,
            "buyer": buyer,
        }
        self.pending_transactions.append(tx)
        return self.last_block["index"] + 1

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

    def verify_ticket(self, ticket_id: str) -> Dict[str, Any] | None:
        for block in self.chain:
            for tx in block["transactions"]:
                if tx["ticket_id"] == ticket_id:
                    return tx
        return None


# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="🎟️ Blockchain Ticketing", layout="wide")

# Initialize blockchain
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

bc: Blockchain = st.session_state.blockchain

st.title("🎟️ Blockchain-based Event Ticketing System")

# Blockchain status
col1, col2 = st.columns(2)
col1.metric("Chain Length", len(bc.chain))
col2.metric("Is Chain Valid?", "✅ Yes" if bc.is_chain_valid() else "❌ No")

# --- Issue New Ticket ---
st.header("➕ Issue New Ticket")
with st.form("ticket_form", clear_on_submit=True):
    organizer = st.text_input("Organizer")
    event = st.text_input("Event Name")
    ticket_id = st.text_input("Ticket ID (must be unique)")
    buyer = st.text_input("Buyer Name")
    submitted = st.form_submit_button("Generate Ticket & Mine Block")
    if submitted and organizer and event and ticket_id and buyer:
        if bc.verify_ticket(ticket_id):
            st.error("❌ Ticket ID already exists! Duplicate not allowed.")
        else:
            bc.new_ticket(organizer, event, ticket_id, buyer)
            block = bc.new_block(proof=123)
            st.success(f"✅ Ticket {ticket_id} added in Block {block['index']}")

            # Generate QR code for ticket
            qr = qrcode.make(ticket_id)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"QR Code for Ticket {ticket_id}")

# --- Verify Ticket ---
st.header("🔍 Verify Ticket Validity")
check_id = st.text_input("Enter Ticket ID to Verify")
if st.button("Check Ticket"):
    result = bc.verify_ticket(check_id)
    if result:
        st.success("✅ Ticket Found!")
        st.json(result)
    else:
        st.error("❌ Invalid or Fake Ticket!")

# --- Explorer ---
st.header("📜 Blockchain Explorer")
for block in reversed(bc.chain):
    index = block.get("index", "N/A")
    with st.expander(f"Block {index}"):
        st.write("Previous Hash:", block.get("previous_hash", "N/A"))
        st.write("Hash:", block.get("hash", "N/A"))
        st.json(block.get("transactions", []))
