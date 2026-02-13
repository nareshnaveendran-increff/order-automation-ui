import streamlit as st
import requests
import json
import time
import os
import base64
import pandas as pd
import random
import string
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="Increff USP Automation", page_icon="🚚", layout="wide")

# --- DEBUG SIDEBAR (To check if Env is working) ---
with st.sidebar:
    st.header("⚙️ System Status")
    env_check = os.getenv("SEARCH_INV_USER")
    if env_check:
        st.success("✅ .env Loaded Successfully")
    else:
        st.error("❌ .env NOT FOUND or EMPTY")
        st.info("Ensure the .env file is in the same folder as app.py")

# --- Helper Functions ---
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

def generate_random_id(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_item_code(prefix="xyz"):
    return prefix + ''.join(random.choices(string.digits, k=4))

# --- Credentials Mapping ---
CREDS = {
    "SEARCH_INV": {"user": os.getenv("SEARCH_INV_USER"), "pass": os.getenv("SEARCH_INV_PASS")},
    "UPDATE_INV": {"user": os.getenv("UPDATE_INV_USER"), "pass": os.getenv("UPDATE_INV_PASS")},
    "CREATE_ORDER": {"user": os.getenv("CREATE_ORDER_USER"), "pass": os.getenv("CREATE_ORDER_PASS")},
    "PACK_DISPATCH": {"user": os.getenv("PACK_DISPATCH_USER"), "pass": os.getenv("PACK_DISPATCH_PASS")},
    "SUB_ORDER_SEARCH": {
        "user": os.getenv("OMNI_USER"), 
        "pass": os.getenv("OMNI_PASS"), 
        "domain": os.getenv("OMNI_DOMAIN"), 
        "client": os.getenv("OMNI_CLIENT")
    },
    "CANCEL_ORDER_CUST": {"user": os.getenv("CREATE_ORDER_USER"), "pass": os.getenv("CREATE_ORDER_PASS")},
    "CANCEL_ORDER_SELLER": {"user": os.getenv("PACK_DISPATCH_USER"), "pass": os.getenv("PACK_DISPATCH_PASS")},
    "CREATE_RETURN": {"user": os.getenv("CREATE_ORDER_USER"), "pass": os.getenv("CREATE_ORDER_PASS")},
    "SEARCH_RETURN": {
        "user": os.getenv("OMNI_USER"), 
        "pass": os.getenv("OMNI_PASS"), 
        "domain": os.getenv("OMNI_DOMAIN"), 
        "client": os.getenv("OMNI_CLIENT")
    },
    "ORDER_STATUS_BULK": {
        "user": os.getenv("OMNI_USER"), 
        "pass": os.getenv("OMNI_PASS"), 
        "domain": os.getenv("OMNI_DOMAIN")
    },
    "PROCESS_RETURN": {"user": os.getenv("PACK_DISPATCH_USER"), "pass": os.getenv("PACK_DISPATCH_PASS")},
    "CREATE_ARTICLE": {"user": os.getenv("CREATE_ARTICLE_USER"), "pass": os.getenv("CREATE_ARTICLE_PASS")},
    "CREATE_MP": {
        "user": os.getenv("OMNI_USER"), 
        "pass": os.getenv("OMNI_PASS"), 
        "domain": os.getenv("OMNI_DOMAIN")
    },
    "CREATE_EFS": {"user": os.getenv("PACK_DISPATCH_USER"), "pass": os.getenv("PACK_DISPATCH_PASS")}
}

URLS = {
    "SEARCH": "https://staging-common.omni.increff.com/assure-magic2/inventories",
    "UPDATE": "https://staging-common-assure.increff.com/assure-magic2/usp/inventories/absolute",
    "CREATE": "https://staging-common.omni.increff.com/assure-magic2/orders/outward",
    "PACK": "https://staging-common-assure.increff.com/assure-magic2/usp/order/pack",
    "HANDOVER": "https://staging-common-assure.increff.com/assure-magic2/ewms/push/usp/handover/combined",
    "SUB_ORDER_SEARCH": "https://staging1.omni.increff.com/oms/orders/outward/sub-orders/search",
    "CANCEL_CUST_BASE": "https://staging-common.omni.increff.com/assure-magic2/orders",
    "CANCEL_SELLER": "https://staging-common-assure.increff.com/assure-magic2/usp/order/cancel",
    "RETURN_ORDER": "https://staging-common.omni.increff.com/assure-magic2/return/return-orders",
    "RETURN_SEARCH": "https://staging1.omni.increff.com/oms/returnOrders/search",
    "BULK_ORDER_SEARCH": "https://staging1.omni.increff.com/oms/usp/order/get-orders",
    "PROCESS_RETURN": "https://staging-common-assure.increff.com/assure-magic2/usp/return",
    "MASTER_ARTICLE": "https://staging-common.omni.increff.com/assure-magic2/master/articles",
    "MASTER_MP": "https://staging1.omni.increff.com/cims/skulisting?clientChannelId=3552&status=ENABLED",
    "MASTER_EFS": "https://staging-common-assure.increff.com/assure-magic2/usp/listing/create"
}

# --- Styling & Headers ---
st.markdown("""<style>
    .super-header { color: #d32f2f; font-size: 2.5rem; font-weight: 800; text-align: center; }
    .step-card { background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; }
    .stock-card { background: #fdf2f2; border: 1px solid #d32f2f; padding: 10px; border-radius: 8px; text-align: center; }
    </style>""", unsafe_allow_html=True)

st.markdown('<h1 class="super-header">Increff USP Automation</h1>', unsafe_allow_html=True)

# --- Session State ---
if 'inv_res' not in st.session_state: st.session_state.inv_res = []

# --- 7. Main Tabs ---
t0, t1, t2, t3, t4, t5, t6 = st.tabs([
    "👑 Master", "📊 Inventory management", "🚀 Order Fulfilment", 
    "📦 Order Manager", "🛑 Order Cancellation", "🔄 Returns", "📋 Logs"
])

# --- TAB 0: MASTER ---
with t0:
    m_tabs = st.tabs(["➕ Create Article", "🛍️ Create MP Listing", "📦 Create EFS Listing"])
    with m_tabs[0]:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("Create New Article Master")
        c_sku_id = st.text_input("Enter Client SKU ID", placeholder="e.g. LEVI11", key="mast_art_sku")
        if st.button("🚀 Create Article"):
            if c_sku_id:
                article_payload = {"articleMasters": [{"channelSkuCode": c_sku_id, "clientSkuId": c_sku_id, "channelSerialNo": c_sku_id, "barcode": c_sku_id, "category": "BOTTOMS", "brand": "10", "isUom": False, "styleCode": "LEVI1", "mrp": 500, "hsn": "6110200000", "name": "501 '90S TWISTED SISTER SELVEDGE", "taxRule": "GST_5", "size": "29", "color": "28", "isPerishable": False, "isVirtual": False, "isBundled": False, "isSerialCodeRequired": False}]}
                headers = {'authUsername': CREDS["CREATE_ARTICLE"]["user"], 'authPassword': CREDS["CREATE_ARTICLE"]["pass"], 'Content-Type': 'application/json'}
                try:
                    res = requests.post(URLS["MASTER_ARTICLE"], headers=headers, json=article_payload)
                    if res.status_code in [200, 201, 204]:
                        st.success(f"Article Created (Status: {res.status_code})")
                        if res.text.strip(): st.json(res.json())
                    else: st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e: st.error(f"Execution Error: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with m_tabs[1]:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("🛍️ Create MP Listing")
        mp_sku_id = st.text_input("Enter Client SKU ID", key="mast_mp_sku")
        if st.button("🛍️ Create Listing", key="btn_create_mp"):
            if mp_sku_id:
                mp_payload = [{"clientSkuId": mp_sku_id, "channelSerialNo": mp_sku_id, "channelSkuId": mp_sku_id, "clientId": 1200063685, "channelId": "NOON"}]
                headers = {'authUsername': CREDS["CREATE_MP"]["user"], 'authPassword': CREDS["CREATE_MP"]["pass"], 'authdomainname': CREDS["CREATE_MP"]["domain"], 'Content-Type': 'application/json'}
                try:
                    res = requests.post(URLS["MASTER_MP"], headers=headers, json=mp_payload)
                    if res.status_code in [200, 201]: st.success("MarketPlace Listing created")
                except Exception as e: st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

    with m_tabs[2]:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("📦 Create EFS Listing")
        efs_sku_id = st.text_input("Enter Channel SKU Code", key="mast_efs_sku")
        if st.button("📦 Create Listing", key="btn_create_efs"):
            if efs_sku_id:
                efs_payload = {"skuListings": [{"channelSkuCode": efs_sku_id, "channelSerialNo": efs_sku_id, "barcode": efs_sku_id}]}
                headers = {'authUsername': CREDS["CREATE_EFS"]["user"], 'authPassword': CREDS["CREATE_EFS"]["pass"], 'Content-Type': 'application/json'}
                try:
                    res = requests.post(URLS["MASTER_EFS"], headers=headers, json=efs_payload)
                    if res.status_code in [200, 201]: st.success("EFS Listing created")
                except Exception as e: st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 1: INVENTORY MANAGEMENT ---
with t1:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("🔍 Check Live Inventory")
    s_col1, s_col2 = st.columns([4, 1])
    with s_col1:
        search_skus = st.text_input("Enter SKU Codes", key="inv_search_input", label_visibility="collapsed")
    with s_col2:
        if st.button("Check Stock"):
            sku_list = [s.strip() for s in search_skus.split(",") if s.strip()]
            if sku_list:
                res = requests.post(URLS["SEARCH"], headers={'authUsername': CREDS["SEARCH_INV"]["user"], 'authPassword': CREDS["SEARCH_INV"]["pass"], 'Content-Type': 'application/json'}, json={"locationCode": "WHBGN21", "channelSkuCodes": sku_list})
                if res.status_code == 200: st.session_state.inv_res = res.json().get("inventories", [])
    if st.session_state.inv_res:
        st.write("##")
        cols = st.columns(len(st.session_state.inv_res))
        for idx, item in enumerate(st.session_state.inv_res):
            with cols[idx]:
                st.markdown(f'<div class="stock-card"><div class="stock-label">Stock</div><div class="stock-value">{item.get("qcPassAvailableQuantity", 0)}</div><div class="stock-sku">{item.get("channelSkuCode")}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("🆙 Update Absolute Inventory")
    u_col1, u_col2, u_col3 = st.columns([2, 1, 1])
    with u_col1: single_up_sku = st.text_input("Channel SKU Code", key="up_sku_input")
    with u_col2: single_up_qty = st.text_input("Quantity", key="up_qty_input")
    with u_col3:
        st.write("##")
        if st.button("Update Inventory", key="btn_up_inv"):
            res = requests.put(URLS["UPDATE"], headers={'authUsername': CREDS["UPDATE_INV"]["user"], 'authPassword': CREDS["UPDATE_INV"]["pass"], 'Content-Type': 'application/json'}, json={"locationCode": "1992", "products": [{"channelSkuCode": single_up_sku, "quantity": single_up_qty}]})
            if res.status_code == 200: st.success("Inventory Updated!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: ORDER FULFILMENT ---
with t2:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("🛒 Create New Order")
    f_col1, f_col2 = st.columns(2)
    sku_qty_input = f_col1.text_input("Mapping (SKU:Qty)", key="f_map")
    order_id_input = f_col2.text_input("Order ID", key="f_id")
    if st.button("Create Order"):
        try:
            mapping = [item.strip() for item in sku_qty_input.split(",") if ":" in item]
            sku_map = {p.split(":")[0].strip(): int(p.split(":")[1].strip()) for p in mapping}
            if sku_map:
                now_dt = datetime.now(); ct = now_dt.strftime("%Y-%m-%dT%H:%M:%S.000+05:30"); dt = (now_dt + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                payload = {"parentOrderCode": order_id_input, "locationCode": "WHBGN21", "orderCode": order_id_input, "orderTime": ct, "orderType": "SO", "qcStatus": "PASS", "paymentMethod": "COD", "onHold": False, "startProcessingTime": ct, "dispatchByTime": dt, "isSplitRequired": "false", "packType": "PIECE", "shippingAddress": {"name": "Naresh", "line1": "Dubai", "city": "Dubai", "zip": "000000", "country": "UAE", "phone": "9999999999"}, "billingAddress": {"name": "Naresh", "line1": "Dubai", "city": "Dubai", "zip": "000000", "country": "UAE", "phone": "9999999999"}, "orderItems": [{"channelSkuCode": k, "orderItemCode": k, "quantity": v, "sellerDiscountPerUnit": 10, "channelDiscountPerUnit": 10, "sellingPricePerUnit": 150, "shippingChargePerUnit": 20, "giftOptions": {"giftwrapRequired": False, "giftMessage": False, "giftChargePerUnit": None}} for k, v in sku_map.items()], "taxBreakupForms": [{"channelSkuId": k, "baseSellingPricePerUnit": 150.00, "taxItemForms": [{"type": "VAT", "rate": 5, "taxPerUnit": 2.13}]} for k, v in sku_map.items()], "orderCustomAttributes": {"currency": "AED"}}
                res = requests.post(URLS["CREATE"], headers={'authUsername': CREDS["CREATE_ORDER"]["user"], 'authPassword': CREDS["CREATE_ORDER"]["pass"], 'Content-Type': 'application/json'}, json=payload)
                if res.status_code in [200, 201]:
                    st.session_state.order_id, st.session_state.f_sku_map = order_id_input, sku_map
                    st.success(f"Order Created: {order_id_input}")
                else: st.error(res.text)
        except Exception as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("📦 Pack & Dispatch")
    if not st.session_state.order_id:
        st.warning("⚠️ Please create an order first")
    else:
        if st.button("📦 Execute Pack & Dispatch"):
            p_res = requests.post(URLS["PACK"], headers={'authUsername': CREDS["PACK_DISPATCH"]["user"], 'authPassword': CREDS["PACK_DISPATCH"]["pass"], 'Content-Type': 'application/json'}, json={"orderCode": st.session_state.order_id, "locationCode": "1992", "channelName": "NOON", "shipmentItems": [{"channelSkuCode": k, "quantityToPack": str(v)} for k, v in st.session_state.f_sku_map.items()]})
            if p_res.status_code == 200:
                data = p_res.json()
                st.session_state.om_inv_url, st.session_state.om_lab_url = data.get("invoiceUrl"), data.get("shippingLabel", {}).get("shippingLabelUrl")
                requests.post(URLS["HANDOVER"], headers={'authUsername': CREDS["PACK_DISPATCH"]["user"], 'authPassword': CREDS["PACK_DISPATCH"]["pass"], 'Content-Type': 'application/json'}, json={"channelName": "NOON", "locationCode": "1992", "orderCodes": [st.session_state.order_id], "transporter": "SELF"})
                
                # Show Truck Animation
                st.session_state.show_truck = True
                st.rerun()

        # Animation Trigger
        if st.session_state.show_truck:
            st.markdown('<div class="dispatch-text-bubble">Order Dispatched</div>', unsafe_allow_html=True)
            st.markdown('<div class="dispatch-anim">🚚💨</div>', unsafe_allow_html=True)
            time.sleep(6) # Wait for truck to finish crossing
            st.session_state.show_truck = False
            st.rerun()

        if st.session_state.om_inv_url or st.session_state.om_lab_url:
            st.divider()
            c1, c2 = st.columns(2)
            if st.session_state.om_inv_url:
                inv_bytes = download_and_rename(st.session_state.om_inv_url, st.session_state.order_id, "Invoice")
                if inv_bytes:
                    c1.download_button(label="📥 Invoice", data=inv_bytes, file_name=f"{st.session_state.order_id}_Invoice.pdf", mime="application/pdf", use_container_width=True)
            if st.session_state.om_lab_url:
                lab_bytes = download_and_rename(st.session_state.om_lab_url, st.session_state.order_id, "shipLabel")
                if lab_bytes:
                    c2.download_button(label="📥 Shipping Label", data=lab_bytes, file_name=f"{st.session_state.order_id}_shipLabel.pdf", mime="application/pdf", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: ORDER MANAGER ---
with t3:
    # ADDED SUB-TABS: "📦 Pack Existing Order", "📥 Bulk Order Creation", "🔍 Search Specific Order", "🗓️ Last 7 Days Status"
    om_t1, om_bulk, om_t2, om_t3 = st.tabs(["📦 Pack Existing Order", "📥 Bulk Order Creation", "🔍 Search Specific Order", "🗓️ Last 7 Days Status"])
    
    with om_t1:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns(3)
        po, ps, pq = pc1.text_input("Order Code", key="poid"), pc2.text_input("SKU", key="psku"), pc3.text_input("Qty", key="pqty")
        if st.button("Pack Order"):
            p_headers = {'authUsername': CREDS["PACK_DISPATCH"]["user"], 'authPassword': CREDS["PACK_DISPATCH"]["pass"], 'Content-Type': 'application/json'}
            p_res = requests.post(URLS["PACK"], headers=p_headers, json={"orderCode": po, "locationCode": "1992", "channelName": "NOON", "shipmentItems": [{"channelSkuCode": ps, "quantityToPack": str(pq)}]})
            if p_res.status_code == 200:
                requests.post(URLS["HANDOVER"], headers=p_headers, json={"channelName": "NOON", "locationCode": "1992", "orderCodes": [po], "transporter": "SELF"})
                d = p_res.json()
                st.session_state.om_inv_url, st.session_state.om_lab_url = d.get("invoiceUrl"), d.get("shippingLabel", {}).get("shippingLabelUrl")
                st.success("Order packed and dispatched")
        if st.session_state.om_inv_url or st.session_state.om_lab_url:
            c1, c2 = st.columns(2)
            if st.session_state.om_inv_url:
                inv_bytes = download_and_rename(st.session_state.om_inv_url, po, "Invoice")
                if inv_bytes: c1.download_button(label="📥 Invoice", data=inv_bytes, file_name=f"{po}_Invoice.pdf", mime="application/pdf")
            if st.session_state.om_lab_url:
                lab_bytes = download_and_rename(st.session_state.om_lab_url, po, "shipLabel")
                if lab_bytes: c2.download_button(label="📥 Shipping Label", data=lab_bytes, file_name=f"{po}_shipLabel.pdf", mime="application/pdf")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ADDED BULK CREATION LOGIC ---
    with om_bulk:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.subheader("🚀 High-Volume Bulk Order Automator")
        
        # UI Alignment
        col_sku, col_count, col_dist = st.columns([2, 1, 1.5])
        
        with col_sku:
            bulk_skus_input = st.text_area("SKU Entry (Comma separated)", placeholder="SKU1, SKU2, SKU3...", height=200, key="bulk_sku_list_neat")
        
        with col_count:
            order_count_input = st.number_input("Orders to Create", 1, 1000, 10, key="bulk_ord_count_neat")
            st.info("Limit: 1000 orders/execution")
            
        with col_dist:
            st.markdown("##### Distribution Logic")
            b_min_skus = st.number_input("Min SKUs/Order", 1, 20, 1)
            b_max_skus = st.number_input("Max SKUs/Order", 1, 20, 2)
            b_min_qty = st.number_input("Min Qty/SKU", 1, 100, 5)
            b_max_qty = st.number_input("Max Qty/SKU", 1, 100, 5)

        st.divider()
        if st.button("🔥 Create Bulk Orders"):
            sku_list = [s.strip() for s in bulk_skus_input.split(",") if s.strip()]
            
            if not sku_list:
                st.error("Missing Data: Please enter at least one SKU.")
            else:
                headers = {'authUsername': CREDS["CREATE_ORDER"]["user"], 'authPassword': CREDS["CREATE_ORDER"]["pass"], 'Content-Type': 'application/json'}
                summary_data = []
                success_count = 0
                
                with st.status("Processing Order Pipeline...", expanded=True) as status:
                    progress_bar = st.progress(0)
                    for i in range(int(order_count_input)):
                        order_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                        now_dt = datetime.now()
                        iso_now = now_dt.strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                        iso_24h = (now_dt + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
                        
                        # Determine exact number of unique SKUs to pick based on available list
                        desired_sku_count = random.randint(b_min_skus, b_max_skus)
                        actual_sku_count = min(len(sku_list), desired_sku_count)
                        picked_skus = random.sample(sku_list, actual_sku_count)
                        
                        items = []
                        sku_qty_details = []
                        for sku in picked_skus:
                            qty = random.randint(b_min_qty, b_max_qty)
                            items.append({
                                "channelSkuCode": sku,
                                "orderItemCode": sku,
                                "quantity": qty,
                                "sellerDiscountPerUnit": 10,
                                "channelDiscountPerUnit": 10,
                                "sellingPricePerUnit": 150,
                                "shippingChargePerUnit": 20,
                                "giftOptions": {"giftwrapRequired": False, "giftMessage": False, "giftChargePerUnit": None}
                            })
                            sku_qty_details.append(f"{sku}({qty})")
                        
                        payload = {
                            "parentOrderCode": order_code, "locationCode": "WHBGN21", "orderCode": order_code, "orderTime": iso_now,
                            "orderType": "SO", "isPriority": False, "gift": False, "onHold": False, "qcStatus": "PASS",
                            "dispatchByTime": iso_24h, "startProcessingTime": iso_now, "paymentMethod": "COD", "isSplitRequired": "false",
                            "packType": "PIECE",
                            "shippingAddress": {"name": "Naresh", "line1": "Dubai Main Road", "line2": "Dubai Bus Stand", "line3": "", "city": "Dubai", "state": "", "zip": "000000", "country": "UAE", "email": "customer@gmail.com", "phone": "9999999999"},
                            "billingAddress": {"name": "Naresh", "line1": "Dubai Main Road", "line2": "Dubai Bus Stand", "line3": "", "city": "Dubai", "state": "", "zip": "000000", "country": "UAE", "email": "customer@increff.com", "phone": "9999999999"},
                            "orderItems": items
                        }
                        
                        try:
                            res = requests.post(URLS["CREATE"], headers=headers, json=payload)
                            if res.status_code in [200, 201]:
                                success_count += 1
                                summary_data.append({"Order Code": order_code, "SKUs & Qty": ", ".join(sku_qty_details)})
                        except: pass
                        progress_bar.progress((i + 1) / order_count_input)
                    
                    status.update(label=f"Done! Created {success_count} orders.", state="complete")
                
                if summary_data:
                    st.success("✅ Orders Generated Successfully")
                    st.table(pd.DataFrame(summary_data))
        st.markdown('</div>', unsafe_allow_html=True)
        
    with om_t2:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        ci = st.text_input("Channel Order ID", key="omsi")
        if st.button("Check Status"):
            res = requests.post(URLS["SUB_ORDER_SEARCH"], headers={'authUsername': CREDS["SUB_ORDER_SEARCH"]["user"], 'authdomainname': CREDS["SUB_ORDER_SEARCH"]["domain"], 'authPassword': CREDS["SUB_ORDER_SEARCH"]["pass"], 'clientid': CREDS["SUB_ORDER_SEARCH"]["client"], 'Content-Type': 'application/json'}, json={"pageNo": 1, "pageSize": 100, "channelOrderId": ci})
            if res.status_code == 200:
                data = res.json(); orders = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
                st.table(pd.DataFrame([{"channelOrderId": o.get("channelOrderId"), "channelId": o.get("channelId") or o.get("channelName"), "status": o.get("status")} for o in orders]))
        st.markdown('</div>', unsafe_allow_html=True)
    with om_t3:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        if st.button("Fetch 7-Day Orders"):
            e, s = datetime.now(), datetime.now() - timedelta(days=7)
            res = requests.post(URLS["BULK_ORDER_SEARCH"], headers={'authUsername': CREDS["ORDER_STATUS_BULK"]["user"], 'authPassword': CREDS["ORDER_STATUS_BULK"]["pass"], 'AuthDomainname': CREDS["ORDER_STATUS_BULK"]["domain"], 'Content-Type': 'application/json'}, json={"sortBy": "ID", "sortOrder": "DESC", "pageSize": 100, "pageNo": 1, "minOrderedAt": s.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "maxOrderedAt": e.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "fulfillmentLocationId": 1200063688})
            if res.status_code == 200:
                data = res.json(); ol = data if isinstance(data, list) else (data.get("orders") or data.get("orderList") or [])
                if ol:
                    df = pd.DataFrame([{"channelOrderId": o.get("channelOrderId"), "channelId": o.get("channelName") or o.get("channelId"), "status": o.get("status")} for o in ol])
                    st.table(df)
                    st.divider()
                    st.subheader("📊 Status Breakdown")
                    st.bar_chart(df['status'].value_counts())
                else: st.warning("No orders found for the last 7 days.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: ORDER CANCELLATION ---
with t4:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    ct = st.radio("Reason", ["Seller Cancellation", "Customer Cancellation"], horizontal=True)
    cl1, cl2, cl3 = st.columns(3)
    oid, sk, qty = cl1.text_input("Order ID", key="can_o"), cl2.text_input("SKU", key="can_s"), cl3.text_input("Qty", key="can_q")
    if st.button("Execute Cancellation"):
        if ct == "Customer Cancellation":
            u, h = f"{URLS['CANCEL_CUST_BASE']}/{oid}/cancel", {'authUsername': CREDS["CANCEL_ORDER_CUST"]["user"], 'authPassword': CREDS["CANCEL_ORDER_CUST"]["pass"], 'Content-Type': 'application/json'}
            p = {"locationCode": "WHBGN21", "orderItems": [{"channelSkuCode": sk, "cancelledQuantity": int(qty), "orderItemCode": sk}]}
        else:
            u, h = URLS["CANCEL_SELLER"], {'authUsername': CREDS["CANCEL_ORDER_SELLER"]["user"], 'authPassword': CREDS["CANCEL_ORDER_SELLER"]["pass"], 'Content-Type': 'application/json'}
            p = {"orderCode": oid, "locationCode": "1992", "channelName": "NOON", "orderItems": [{"channelSkuCode": sk, "cancelledQuantity": str(qty)}]}
        res = requests.put(u, headers=h, json=p)
        if res.status_code in [200, 204]: st.success("Cancelled!")
        else: st.error(res.text)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 5: RETURNS ---
with t5:
    rt1, rt2, rt3 = st.tabs(["➕ Create Return", "🔍 Search Return", "🔄 Return Processing"])
    with rt1:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        r1, r2 = st.columns(2); fo, ab = r1.text_input("Forward Order Code", key="rfo"), r2.text_input("AWB", key="raw")
        sq = st.text_input("SKU:Qty", key="rsq")
        if st.button("Create Return"):
            it = []
            for p in sq.split(","):
                s, q = p.split(":")[0].strip(), int(p.split(":")[1].strip())
                for _ in range(q): it.append({"itemCode": generate_item_code("RET-"), "reason": "damaged", "channelSkuCode": s})
            res = requests.post(URLS["RETURN_ORDER"], headers={'authUsername': CREDS["CREATE_RETURN"]["user"], 'authPassword': CREDS["CREATE_RETURN"]["pass"], 'Content-Type': 'application/json'}, json={"forwardOrderCode": fo, "returnOrderCode": f"r1-{fo}", "locationCode": "WHBGN21", "orderItems": it, "orderType": "CUSTOMER_RETURN", "awbNumber": ab, "transporter": "SELF", "dropAddress": {"name": "Naresh", "line1": "address"}, "pickupAddress": {"name": "Naresh", "line1": "address"}})
            if res.status_code in [200, 201]: st.success("Return Created!")
        st.markdown('</div>', unsafe_allow_html=True)
    with rt2:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        if st.button("Search Returns (7D)"):
            e, s = datetime.now(), datetime.now() - timedelta(days=7)
            res = requests.post(URLS["RETURN_SEARCH"], headers={'authUsername': CREDS["SEARCH_RETURN"]["user"], 'authdomainname': CREDS["SEARCH_RETURN"]["domain"], 'authPassword': CREDS["SEARCH_RETURN"]["pass"], 'clientid': CREDS["SEARCH_RETURN"]["client"], 'Content-Type': 'application/json'}, json={"startDate": s.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "endDate": e.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "sortBy": "ID", "sortOrder": "DESC", "maxCount": 100, "fulfillmentLocationId": 1200063688})
            if res.status_code == 200:
                d = res.json(); rs = d if isinstance(d, list) else (d.get("returnOrderList") or [])
                st.table(pd.DataFrame([{"channelOrderId": r.get("channelOrderId"), "channelReturnId": r.get("channelReturnId"), "trackingId": r.get("trackingId"), "status": r.get("status")} for r in rs]))
        st.markdown('</div>', unsafe_allow_html=True)
    with rt3:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2); pf, pr = c1.text_input("Forward Order Code", key="pfo"), c2.text_input("Return Order Code", key="pro")
        c3, c4 = st.columns(2); pa, ps = c3.text_input("Tracking Number", key="pab"), c4.text_input("SKU", key="psk")
        pq = st.selectbox("QC Status", ["PASS", "FAIL"], key="pqc")
        if st.button("Process Return"):
            res = requests.post(URLS["PROCESS_RETURN"], headers={'authUsername': CREDS["PROCESS_RETURN"]["user"], 'authPassword': CREDS["PROCESS_RETURN"]["pass"], 'Content-Type': 'application/json'}, json={"returnOrderCode": pr, "forwardOrderCode": pf, "locationCode": "1992", "channelName": "NOON", "awbNumber": pa, "transporter": "SELF", "orderItems": [{"returnItemCode": generate_item_code("xyz"), "channelSkuCode": ps, "qcStatus": pq, "qcReason": "DAMAGED"}]})
            if res.status_code in [200, 201]: st.success("Return Processed Successfully!")
            else: st.error(res.text)
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 6: LOGS ---
with t6:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("📋 ELK Logs Search (Last 30 Mins)")
    l1, l2, l3 = st.columns(3)
    lk = l1.text_input("Keyword", key="lk_main")
    lr = l2.text_input("Request Name (Optional)", key="lk_req")
    ls = l3.text_input("Status (Optional)", key="lk_stat")
    st.info("**Instructions:** Use `admin` / `admin` to login.")
    if lk:
        lucene_query = f'"{lk}"'
        if lr: lucene_query += f' AND request_name: *{lr}*'
        if ls: lucene_query += f' AND status: *{ls}*'
        query_encoded = urllib.parse.quote(lucene_query)
        elk_url = f"https://elk-dev.nextscm.com/app/kibana#/discover?_g=(time:(from:now-30m,to:now))&_a=(query:(language:lucene,query:'{query_encoded}'))"
        st.markdown(f'<div style="margin-top: 20px;"><p>Query: <code>{lucene_query}</code></p><a href="{elk_url}" target="_blank" class="elk-button">🔍 Open ELK Search</a></div>', unsafe_allow_html=True)
    else:
        st.warning("Please enter a keyword to generate the search link.")
    st.markdown('</div>', unsafe_allow_html=True)
