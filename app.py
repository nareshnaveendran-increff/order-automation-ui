import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta

# --- Configuration & Credentials ---
CREDS = {
    "SEARCH_INV": {"user": "NOON-1200063685", "pass": "73722c6c-c716-489c-88b8-5347132f5745"},
    "CREATE_ORDER": {"user": "NOON-1200063685", "pass": "73722c6c-c716-489c-88b8-5347132f5745"},
    "PACK_DISPATCH": {"user": "LEVI_EFS-1200063685", "pass": "d958a6d2-e6f5-4c89-86f7-26d21654f878"}
}

URLS = {
    "SEARCH": "https://staging-common.omni.increff.com/assure-magic2/inventories",
    "CREATE": "https://staging-common.omni.increff.com/assure-magic2/orders/outward",
    "PACK": "https://staging-common-assure.increff.com/assure-magic2/usp/order/pack",
    "HANDOVER": "https://staging-common-assure.increff.com/assure-magic2/ewms/push/usp/handover/combined"
}

# --- Page Setup ---
st.set_page_config(page_title="Increff USP Auto Fulfillment", page_icon="🚀")

# --- Logos and Title ---
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://www.increff.com/wp-content/uploads/2022/03/Increff-Logo-1.png", width=120) # Increff Logo
with col2:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Levi%27s_logo.svg/2560px-Levi%27s_logo.svg.png", width=80) # Levis Logo

st.title("🚀 Increff USP Auto Fulfillment")

# --- Initialize Session State ---
if 'phase' not in st.session_state:
    st.session_state.phase = 'search'
if 'inventory_results' not in st.session_state:
    st.session_state.inventory_results = []
if 'sku_map' not in st.session_state:
    st.session_state.sku_map = {}
if 'dispatch_success' not in st.session_state:
    st.session_state.dispatch_success = False

# --- Helper: Confetti Script (7 Seconds) ---
def celebration_js():
    st.components.v1.html("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <script>
        var end = Date.now() + (7 * 1000);
        var colors = ['#2e7d32', '#ffffff', '#4caf50', '#ff0000', '#ffd700'];
        (function frame() {
          confetti({ particleCount: 5, angle: 60, spread: 55, origin: { x: 0 }, colors: colors });
          confetti({ particleCount: 5, angle: 120, spread: 55, origin: { x: 1 }, colors: colors });
          if (Date.now() < end) { requestAnimationFrame(frame); }
        }());
    </script>
    """, height=0)

# --- PHASE 1: SEARCH INVENTORY ---
st.header("1. Search Inventory")
search_skus = st.text_input("Enter SKUs for Inventory (comma separated):", placeholder="e.g. LEVI, SKU2")

if st.button("Search Inventory"):
    sku_list = [s.strip() for s in search_skus.split(",") if s.strip()]
    if sku_list:
        headers = {'authUsername': CREDS["SEARCH_INV"]["user"], 'authPassword': CREDS["SEARCH_INV"]["pass"], 'Content-Type': 'application/json'}
        payload = {"locationCode": "WHBGN21", "channelSkuCodes": sku_list}
        try:
            res = requests.post(URLS["SEARCH"], headers=headers, json=payload)
            data = res.json()
            inv_list = data.get("inventories", []) if isinstance(data, dict) else data
            
            if inv_list:
                st.session_state.inventory_results = inv_list
                st.session_state.phase = 'create'
            else:
                st.error("Failed")
        except:
            st.error("Failed")
    else:
        st.warning("Please enter at least one SKU.")

# Display Inventory Results
for item in st.session_state.inventory_results:
    st.write(f'Available Quantity: "{item.get("qcPassAvailableQuantity", 0)}"')

# --- PHASE 2: CREATE ORDER ---
if st.session_state.phase in ['create', 'pack']:
    st.markdown("---")
    st.header("2. Create Order")
    sku_qty_map = st.text_input("SKU:Qty Map:", placeholder="LEVI:5, SKU2:3")
    order_code = st.text_input("Order Code:")

    if st.button("Create Order"):
        try:
            mapping_raw = [item.strip() for item in sku_qty_map.split(",") if ":" in item]
            st.session_state.sku_map = {pair.split(":")[0].strip(): int(pair.split(":")[1].strip()) for pair in mapping_raw}
            
            if not st.session_state.sku_map:
                st.error("Invalid Format. Use SKU:Qty (e.g. LEVI:5)")
            else:
                now = datetime.now()
                time_str = now.strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                dispatch_str = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000+05:30")

                payload = {
                    "parentOrderCode": order_code, "locationCode": "WHBGN21", "orderCode": order_code,
                    "orderTime": time_str, "startProcessingTime": time_str, "dispatchByTime": dispatch_str,
                    "orderType": "SO", "isPriority": False, "gift": False, "onHold": False, "qcStatus": "PASS",
                    "paymentMethod": "COD", "isSplitRequired": "false", "packType": "PIECE",
                    "shippingAddress": {"name": "Naresh", "line1": "Dubai", "city": "Dubai", "zip": "000000", "country": "UAE", "email": "customer@gmail.com", "phone": "9999999999"},
                    "billingAddress": {"name": "Naresh", "line1": "Dubai", "city": "Dubai", "zip": "000000", "country": "UAE", "email": "customer@increff.com", "phone": "9999999999"},
                    "orderItems": [{"channelSkuCode": k, "orderItemCode": k, "quantity": v, "sellerDiscountPerUnit": 10, "channelDiscountPerUnit": 10, "sellingPricePerUnit": 150, "shippingChargePerUnit": 20, "giftOptions": {"giftwrapRequired": False, "giftMessage": False, "giftChargePerUnit": None}} for k, v in st.session_state.sku_map.items()],
                    "taxBreakupForms": [{"channelSkuId": k, "baseSellingPricePerUnit": 150.00, "taxItemForms": [{"type": "VAT", "rate": 5, "taxPerUnit": 2.13}]} for k, v in st.session_state.sku_map.items()],
                    "orderCustomAttributes": {"currency": "AED"}
                }
                
                headers = {'authUsername': CREDS["CREATE_ORDER"]["user"], 'authPassword': CREDS["CREATE_ORDER"]["pass"], 'Content-Type': 'application/json'}
                res = requests.post(URLS["CREATE"], headers=headers, json=payload)
                
                if res.status_code in [200, 201]:
                    st.success("Order Created")
                    st.session_state.order_id = order_code
                    st.session_state.phase = 'pack'
                else:
                    st.error("Order Creation Failed")
        except:
            st.error("Error processing request.")

# --- PHASE 3: ORDER PROCESSING ---
if st.session_state.phase == 'pack':
    st.markdown("---")
    st.header("3. Order processing")
    
    # Button is disabled if dispatch was already successful
    if st.button("Pack and Dispatch", disabled=st.session_state.dispatch_success):
        pack_headers = {'authUsername': CREDS["PACK_DISPATCH"]["user"], 'authPassword': CREDS["PACK_DISPATCH"]["pass"], 'Content-Type': 'application/json'}
        pack_payload = {
            "orderCode": st.session_state.order_id, 
            "locationCode": "1992", 
            "channelName": "NOON", 
            "shipmentItems": [{"channelSkuCode": k, "quantityToPack": str(v)} for k, v in st.session_state.sku_map.items()]
        }
        
        p_res = requests.post(URLS["PACK"], headers=pack_headers, json=pack_payload)
        
        if p_res.status_code == 200:
            p_data = p_res.json()
            st.write(f"shippingLabelUrl: {p_data.get('shippingLabelUrl')}")
            st.write(f"invoiceUrl: {p_data.get('invoiceUrl')}")
            
            time.sleep(1.5)
            
            h_payload = {"channelName": "NOON", "locationCode": "1992", "orderCodes": [st.session_state.order_id], "transporter": "SELF"}
            h_res = requests.post(URLS["HANDOVER"], headers=pack_headers, json=h_payload)
            
            if h_res.status_code == 200:
                st.session_state.dispatch_success = True
                st.rerun() # Refresh to disable button and show success
            else:
                st.error(f"Dispatch Failed: {h_res.text}")
        else:
            st.error(f"Packing Failed: {p_res.text}")

# --- FINAL SUCCESS MESSAGE & CELEBRATION ---
if st.session_state.dispatch_success:
    celebration_js()
    st.markdown("<h2 style='color: #2e7d32; text-align: center;'><b>Order Dispatched 🥳🎉</b></h2>", unsafe_allow_html=True)
    if st.button("Start New Order"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()