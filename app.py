import streamlit as st
import requests
import json
import time
import os
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="Increff USP Automation",
    page_icon="🚚",
    layout="wide"
)

# --- 1. HORIZONTAL LOGO ALIGNMENT ---
with st.sidebar:
    current_dir = os.path.dirname(__file__)
    
    # Create two columns in the sidebar for Side-by-Side alignment
    side_col1, side_col2 = st.columns(2)
    
    # Logo 1 - Left Side (Small Size)
    path1 = os.path.join(current_dir, "logo.png") 
    if os.path.exists(path1):
        # width=80 to keep it roughly half the size of the sidebar column
        side_col1.image(path1, width=240) 
    else:
        side_col1.error("logo1 missing")

    # Logo 2 - Right Side (Full Column Width)
    path2 = os.path.join(current_dir, "logo2.png")
    if os.path.exists(path2):
        side_col2.image(path2, use_container_width=True)
    else:
        side_col2.error("logo2 missing")

# --- 2. SUPER COOL UI STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #fcfafb; font-family: 'Inter', sans-serif; }
    
    h1, h2, h3, .stMarkdown p, label { 
        color: #a31d1d !important; 
        font-weight: 700 !important; 
    }

    .main-header {
        background: linear-gradient(90deg, #d32f2f 0%, #ff5252 100%);
        padding: 45px; border-radius: 20px; color: white !important;
        text-align: center; margin-bottom: 40px;
    }
    .main-header h1 { color: white !important; }

    .step-card {
        background: #ffffff; padding: 35px; border-radius: 18px;
        border: 1px solid #ffebee; border-top: 6px solid #ff5252;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 30px;
    }

    .stTextInput>div>div>input {
        background-color: #ffffff !important; color: #000000 !important;
        border: 2px solid #d32f2f !important; border-radius: 10px;
    }

    [data-testid="stMetricValue"] { font-weight: 900; color: #d32f2f !important; font-size: 8rem !important; letter-spacing: -2px; }

    /* Buttons Visibility and Styling */
    .stButton > button {
        background-color: #d32f2f !important;
        color: white !important;
        border-radius: 12px !important;
        height: 4.5em !important;
        width: 100% !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        border: none !important;
        display: block !important;
    }
    
    .secondary-btn div[data-testid="stButton"] > button { background-color: #757575 !important; }
    .cancel-btn div[data-testid="stButton"] > button { background-color: #333333 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- API Config ---
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

if 'phase' not in st.session_state: st.session_state.phase = 'search'
if 'inv_res' not in st.session_state: st.session_state.inv_res = []
if 'sku_map' not in st.session_state: st.session_state.sku_map = {}
if 'dispatch_done' not in st.session_state: st.session_state.dispatch_done = False
if 'order_success_time' not in st.session_state: st.session_state.order_success_time = 0

def celebration_js():
    st.components.v1.html("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <script>
        var end = Date.now() + (7 * 1000);
        (function frame() {
          confetti({ particleCount: 5, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#ff5252', '#d32f2f', '#ffffff'] });
          confetti({ particleCount: 5, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#ff5252', '#d32f2f', '#ffffff'] });
          if (Date.now() < end) { requestAnimationFrame(frame); }
        }());
    </script>
    """, height=0)

st.markdown('<div class="main-header"><h1>⚡ INCREFF USP AUTOMATION</h1></div>', unsafe_allow_html=True)

# 1. Inventory search
with st.container():
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("🏬 1. Inventory search")
    col1, col2 = st.columns([4, 1])
    with col1:
        search_skus = st.text_input("Enter SKU Codes:", placeholder="04511240203432", key="sku_in")
    with col2:
        st.write("##")
        if st.button("🔍 CHECK LIVE STOCK", key="stock_btn"):
            sku_list = [s.strip() for s in search_skus.split(",") if s.strip()]
            if sku_list:
                headers = {'authUsername': CREDS["SEARCH_INV"]["user"], 'authPassword': CREDS["SEARCH_INV"]["pass"], 'Content-Type': 'application/json'}
                res = requests.post(URLS["SEARCH"], headers=headers, json={"locationCode": "WHBGN21", "channelSkuCodes": sku_list})
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.inv_res = data.get("inventories", []) if isinstance(data, dict) else data
                    if st.session_state.inv_res:
                        st.session_state.phase = 'create'
                        st.rerun()
    
    if st.session_state.inv_res:
        cols = st.columns(len(st.session_state.inv_res))
        for i, item in enumerate(st.session_state.inv_res):
            cols[i].metric(label=f"📦 SKU STOCK: {item.get('channelSkuCode')}", value=item.get("qcPassAvailableQuantity", 0))
    st.markdown('</div>', unsafe_allow_html=True)

# 2. Create Outward Order
if st.session_state.phase in ['create', 'pack']:
    with st.container():
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("📝 2. Create Outward Order")
        
        if st.session_state.order_success_time > 0:
            if (time.time() - st.session_state.order_success_time) < 10:
                st.success("✅ Order Created Successfully")
            else:
                st.session_state.order_success_time = 0

        c1_in, col_ord = st.columns(2)
        with c1_in:
            sku_qty_map = st.text_input("Order Map (SKU:Qty):", placeholder="04511240203432:5")
        with col_ord:
            order_code = st.text_input("Unique Order ID:", placeholder="NEGHC-XXXX")

        if st.button("🛒 CREATE OUTWARD ORDER", key="create_btn"):
            try:
                mapping = [item.strip() for item in sku_qty_map.split(",") if ":" in item]
                st.session_state.sku_map = {p.split(":")[0].strip(): int(p.split(":")[1].strip()) for p in mapping}
                if st.session_state.sku_map:
                    now = datetime.now()
                    now_str = now.strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                    dispatch_str = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                    payload = {
                        "parentOrderCode": order_code, "locationCode": "WHBGN21", "orderCode": order_code,
                        "orderTime": now_str, "orderType": "SO", "isPriority": False, "gift": False, "onHold": False,
                        "qcStatus": "PASS", "dispatchByTime": dispatch_str, "startProcessingTime": now_str,
                        "paymentMethod": "COD", "isSplitRequired": "false", "packType": "PIECE",
                        "shippingAddress": {"name": "Naresh", "line1": "Dubai Main Road", "line2": "Dubai Bus Stand", "line3": "", "city": "Dubai", "state": "", "zip": "000000", "country": "UAE", "email": "customer@gmail.com", "phone": "9999999999"},
                        "billingAddress": {"name": "Naresh", "line1": "Dubai Main Road", "line2": "Dubai Bus Stand", "line3": "", "city": "Dubai", "state": "", "zip": "000000", "country": "UAE", "email": "customer@increff.com", "phone": "9999999999"},
                        "orderItems": [{"channelSkuCode": k, "orderItemCode": k, "quantity": v, "sellerDiscountPerUnit": 10, "channelDiscountPerUnit": 10, "sellingPricePerUnit": 150, "shippingChargePerUnit": 20, "giftOptions": {"giftwrapRequired": False, "giftMessage": False, "giftChargePerUnit": None}} for k, v in st.session_state.sku_map.items()],
                        "taxBreakupForms": [{"channelSkuId": k, "baseSellingPricePerUnit": 150.00, "taxItemForms": [{"type": "VAT", "rate": 5, "taxPerUnit": 2.13}]} for k, v in st.session_state.sku_map.items()],
                        "orderCustomAttributes": {"currency": "AED"}
                    }
                    headers = {'authUsername': CREDS["CREATE_ORDER"]["user"], 'authPassword': CREDS["CREATE_ORDER"]["pass"], 'Content-Type': 'application/json'}
                    res = requests.post(URLS["CREATE"], headers=headers, json=payload)
                    if res.status_code in [200, 201]:
                        st.session_state.order_id = order_code
                        st.session_state.phase = 'pack'
                        st.session_state.order_success_time = time.time()
                        st.rerun()
                    else: st.error(f"Creation Failed: {res.text}")
            except Exception as e: st.error(f"Error: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# 3. Order Processing
if st.session_state.phase == 'pack':
    with st.container():
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("⚙️ 3. Order Processing")
        if st.button("📦 Pack and dispatch", key="dispatch_btn", disabled=st.session_state.dispatch_done):
            headers = {'authUsername': CREDS["PACK_DISPATCH"]["user"], 'authPassword': CREDS["PACK_DISPATCH"]["pass"], 'Content-Type': 'application/json'}
            pack_payload = {"orderCode": st.session_state.order_id, "locationCode": "1992", "channelName": "NOON", "shipmentItems": [{"channelSkuCode": k, "quantityToPack": str(v)} for k, v in st.session_state.sku_map.items()]}
            p_res = requests.post(URLS["PACK"], headers=headers, json=pack_payload)
            if p_res.status_code == 200:
                p_data = p_res.json()
                st.code(f"{p_data.get('shippingLabelUrl')}", language=None)
                st.info(f"💰 Invoice: {p_data.get('invoiceUrl')}")
                time.sleep(1.5)
                h_res = requests.post(URLS["HANDOVER"], headers=headers, json={"channelName": "NOON", "locationCode": "1992", "orderCodes": [st.session_state.order_id], "transporter": "SELF"})
                if h_res.status_code == 200:
                    st.session_state.dispatch_done = True
                    st.rerun()
                else: st.error("Handover Failed")
    st.markdown('</div>', unsafe_allow_html=True)

# --- INDEPENDENT ORDER MANAGEMENT SECTION ---
st.markdown("---")
with st.container():
    st.subheader("🛠️ Order Management")
    bot_col1, bot_col2 = st.columns(2)
    with bot_col1:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("📋 Pack the existing order", key="pack_existing"):
            st.warning("Under construction 👷")
        st.markdown('</div>', unsafe_allow_html=True)
    with bot_col2:
        st.markdown('<div class="cancel-btn">', unsafe_allow_html=True)
        if st.button("🛑 Customer Cancellation", key="cancel_order"):
            st.warning("Under construction 👷")
        st.markdown('</div>', unsafe_allow_html=True)

# SUCCESS VIEW
if st.session_state.dispatch_done:
    celebration_js()
    st.markdown('<div style="background: rgba(211, 47, 47, 0.05); padding: 50px; border-radius: 20px; text-align: center; border: 2px solid #ff5252;"><h1 style="color: #d32f2f; margin: 0;">🛵 ORDER DISPATCHED 🥳🎉</h1></div>', unsafe_allow_html=True)
    st.write("##")
    if st.button("🔄 START NEW FULFILLMENT CYCLE", key="reset_btn"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
