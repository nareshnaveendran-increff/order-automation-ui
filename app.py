import streamlit as st
import requests
import json
import time
import os
import base64
from datetime import datetime, timedelta

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="USP Auto",
    page_icon="🚚",
    layout="wide"
)

# --- 2. Helper for High-Quality Logos ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

def set_high_qual_logo(path, height="60px"):
    bin_str = get_base64_of_bin_file(path)
    if bin_str:
        return f'<img src="data:image/png;base64,{bin_str}" style="height: {height}; width: auto; object-fit: contain;">'
    return ""

# --- 3. UI Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #fcfafb; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 5rem !important; padding-bottom: 1rem !important; }

    .header-wrapper { display: flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 20px; }
    .super-header { color: #d32f2f !important; font-size: 3rem !important; font-weight: 800 !important; letter-spacing: -1.8px; margin: 0; text-align: center; flex-grow: 1; }

    .stock-card { background: #fff; border: 2px solid #d32f2f; border-radius: 10px; padding: 10px; text-align: center; box-shadow: 0 2px 8px rgba(211, 47, 47, 0.05); }
    .stock-value { font-size: 2.8rem; color: #d32f2f; font-weight: 900; line-height: 1; margin: 5px 0; }
    .stock-sku { font-size: 0.75rem; color: #888; }

    .step-card { background: #ffffff; padding: 15px 25px; border-radius: 12px; border: 1px solid #eef0f2; box-shadow: 0 2px 10px rgba(0,0,0,0.03); margin-bottom: 8px; }
    
    .stButton > button { background-color: #d32f2f !important; color: white !important; border-radius: 8px !important; font-weight: 700 !important; height: 3em !important; width: 100%; }
    
    .download-link {
        display: inline-block; padding: 0.4em 0.8em; color: #d32f2f !important; text-decoration: none;
        border: 1px solid #d32f2f; border-radius: 8px; font-weight: 600; text-align: center; margin-top: 5px; width: 100%; font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HD Header ---
current_dir = os.path.dirname(__file__)
path_increff = os.path.join(current_dir, "logo.png")
path_levis = os.path.join(current_dir, "logo2.png")

st.markdown(f"""
    <div class="header-wrapper">
        <div style="width: 150px; text-align: left;">{set_high_qual_logo(path_increff, "65px")}</div>
        <h1 class="super-header">Increff USP Automation</h1>
        <div style="width: 150px; text-align: left; padding-left: 20px;">{set_high_qual_logo(path_levis, "55px")}</div>
    </div>
""", unsafe_allow_html=True)

# --- 5. API Configuration ---
CREDS = {
    "SEARCH_INV": {"user": "NOON-1200063685", "pass": "73722c6c-c716-489c-88b8-5347132f5745"},
    "UPDATE_INV": {"user": "LEVI_EFS-1200063685", "pass": "d958a6d2-e6f5-4c89-86f7-26d21654f878"},
    "CREATE_ORDER": {"user": "NOON-1200063685", "pass": "73722c6c-c716-489c-88b8-5347132f5745"},
    "PACK_DISPATCH": {"user": "LEVI_EFS-1200063685", "pass": "d958a6d2-e6f5-4c89-86f7-26d21654f878"}
}

URLS = {
    "SEARCH": "https://staging-common.omni.increff.com/assure-magic2/inventories",
    "UPDATE": "https://staging-common-assure.increff.com/assure-magic2/usp/inventories/absolute",
    "CREATE": "https://staging-common.omni.increff.com/assure-magic2/orders/outward",
    "PACK": "https://staging-common-assure.increff.com/assure-magic2/usp/order/pack",
    "HANDOVER": "https://staging-common-assure.increff.com/assure-magic2/ewms/push/usp/handover/combined"
}

# --- 6. Session State ---
if 'inv_res' not in st.session_state: st.session_state.inv_res = []
if 'order_id' not in st.session_state: st.session_state.order_id = ""

# --- 7. Tabs ---
t1, t2, t3, t4, t5 = st.tabs(["📊 Inventory management", "🚀 Order Fulfilment", "📦 Order Manager", "🛑 Order Cancellation", "🔄 Returns"])

# --- TAB 1: INVENTORY MANAGEMENT ---
with t1:
    # --- Check Inventory ---
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("Inventory Check")
    s_col_in, s_col_btn = st.columns([4, 1.2])
    search_skus = s_col_in.text_input("Enter SKU Codes", placeholder="SKU1, SKU2", key="live_search", label_visibility="collapsed")
    if s_col_btn.button("🔍 Check Stock"):
        sku_list = [s.strip() for s in search_skus.split(",") if s.strip()]
        if sku_list:
            headers = {'authUsername': CREDS["SEARCH_INV"]["user"], 'authPassword': CREDS["SEARCH_INV"]["pass"], 'Content-Type': 'application/json'}
            res = requests.post(URLS["SEARCH"], headers=headers, json={"locationCode": "WHBGN21", "channelSkuCodes": sku_list})
            if res.status_code == 200: st.session_state.inv_res = res.json().get("inventories", [])
    
    if st.session_state.inv_res:
        cols = st.columns(len(st.session_state.inv_res))
        for idx, item in enumerate(st.session_state.inv_res):
            with cols[idx]:
                st.markdown(f'<div class="stock-card"><div class="stock-label">Stock</div><div class="stock-value">{item.get("qcPassAvailableQuantity", 0)}</div><div class="stock-sku">{item.get("channelSkuCode")}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Update Inventory (Single Input) ---
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("Update Inventory")
    u_col1, u_col2 = st.columns(2)
    single_up_sku = u_col1.text_input("Channel SKU Code", key="single_up_sku")
    single_up_qty = u_col2.text_input("Quantity", key="single_up_qty")
    
    if st.button("🆙 UPDATE"):
        if single_up_sku and single_up_qty:
            headers = {'authUsername': CREDS["UPDATE_INV"]["user"], 'authPassword': CREDS["UPDATE_INV"]["pass"], 'Content-Type': 'application/json'}
            up_payload = {
                "locationCode": "1992",
                "products": [{"channelSkuCode": single_up_sku, "quantity": single_up_qty}]
            }
            res = requests.put(URLS["UPDATE"], headers=headers, json=up_payload)
            if res.status_code == 200:
                st.success(f"Successfully updated {single_up_sku} to {single_up_qty}")
            else:
                st.error(f"Update Failed: {res.text}")
        else:
            st.warning("Please provide both SKU and Quantity.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: ORDER FULFILMENT ---
with t2:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("Create Order")
    f_col1, f_col2 = st.columns(2)
    sku_qty_input = f_col1.text_input("Mapping (SKU:Qty)", placeholder="0451...:5", key="f_map")
    order_id_input = f_col2.text_input("Order ID", key="f_id")
    
    if st.button("🛒 Create Order"):
        try:
            mapping = [item.strip() for item in sku_qty_input.split(",") if ":" in item]
            sku_map = {p.split(":")[0].strip(): int(p.split(":")[1].strip()) for p in mapping}
            if sku_map:
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                dispatch = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                payload = {
                    "parentOrderCode": order_id_input, "locationCode": "WHBGN21", "orderCode": order_id_input,
                    "orderTime": now, "orderType": "SO", "isPriority": False, "gift": False, "onHold": False,
                    "qcStatus": "PASS", "dispatchByTime": dispatch, "startProcessingTime": now,
                    "paymentMethod": "COD", "isSplitRequired": "false", "packType": "PIECE",
                    "shippingAddress": {"name": "Naresh", "line1": "Dubai", "city": "Dubai", "zip": "000000", "country": "UAE", "phone": "9999999999"},
                    "billingAddress": {"name": "Naresh", "line1": "Dubai", "city": "Dubai", "zip": "000000", "country": "UAE", "phone": "9999999999"},
                    "orderItems": [{"channelSkuCode": k, "orderItemCode": k, "quantity": v, "sellerDiscountPerUnit": 10, "channelDiscountPerUnit": 10, "sellingPricePerUnit": 150, "shippingChargePerUnit": 20, "giftOptions": {"giftwrapRequired": False, "giftMessage": False, "giftChargePerUnit": None}} for k, v in sku_map.items()],
                    "taxBreakupForms": [{"channelSkuId": k, "baseSellingPricePerUnit": 150.00, "taxItemForms": [{"type": "VAT", "rate": 5, "taxPerUnit": 2.13}]} for k, v in sku_map.items()],
                    "orderCustomAttributes": {"currency": "AED"}
                }
                headers = {'authUsername': CREDS["CREATE_ORDER"]["user"], 'authPassword': CREDS["CREATE_ORDER"]["pass"], 'Content-Type': 'application/json'}
                res = requests.post(URLS["CREATE"], headers=headers, json=payload)
                if res.status_code in [200, 201]:
                    st.session_state.order_id = order_id_input
                    st.session_state.f_sku_map = sku_map
                    st.success(f"Order {order_id_input} Created")
                else: st.error(f"Failed: {res.text}")
        except Exception as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("Pack & Handover")
    if st.session_state.order_id:
        if st.button("📦 Execute Pack & Dispatch"):
            headers = {'authUsername': CREDS["PACK_DISPATCH"]["user"], 'authPassword': CREDS["PACK_DISPATCH"]["pass"], 'Content-Type': 'application/json'}
            p_payload = {"orderCode": st.session_state.order_id, "locationCode": "1992", "channelName": "NOON", "shipmentItems": [{"channelSkuCode": k, "quantityToPack": str(v)} for k, v in st.session_state.f_sku_map.items()]}
            p_res = requests.post(URLS["PACK"], headers=headers, json=p_payload)
            if p_res.status_code == 200:
                p_data = p_res.json()
                st.session_state.inv_u = p_data.get('invoiceUrl')
                st.session_state.lab_u = p_data.get('shippingLabelUrl')
                requests.post(URLS["HANDOVER"], headers=headers, json={"channelName": "NOON", "locationCode": "1992", "orderCodes": [st.session_state.order_id], "transporter": "SELF"})
                st.balloons(); st.success("Complete")
        if 'inv_u' in st.session_state and st.session_state.inv_u:
            c1, c2 = st.columns(2)
            c1.markdown(f'<a href="{st.session_state.inv_u}" target="_blank" class="download-link">📄 Download Invoice</a>', unsafe_allow_html=True)
            c2.markdown(f'<a href="{st.session_state.lab_u}" target="_blank" class="download-link">🏷️ Download Label</a>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: ORDER MANAGER ---
with t3:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("Order Management")
    m_id = st.text_input("Enter Order ID", key="m_id_in")
    if st.button("📋 Pack Existing Order"): st.info(f"Processing: {m_id}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: ORDER CANCELLATION ---
with t4:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("Order Cancellation")
    c_type = st.radio("Reason", ["Customer Cancellation", "Seller Cancellation"], horizontal=True)
    c_id = st.text_input("Order ID", key="c_id_in")
    if st.button(f"Confirm {c_type}"): st.error(f"Action: {c_type} for {c_id}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 5: RETURNS ---
with t5:
    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("Create Return")
        st.text_input("Order ID", key="ret_id_in")
        st.button("➕ Generate")
    with r2:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("Return Processing")
        st.text_input("Scan ID", key="proc_id_in")
        st.button("Complete")
