from datetime import datetime
import os
import pandas as pd
import sqlite3
import streamlit as st

# --- PAGE CONFIG & ZOHO-INSPIRED ENTERPRISE CSS ---
st.set_page_config(
    page_title="Motor Parts Inventory Suite", page_icon="⚙️", layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #F8F9FA;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .zoho-header {
        background-color: #1A202C;
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .zoho-header h1 {
        color: white;
        font-size: 1.5rem;
        margin: 0;
        font-weight: 600;
    }
    .zoho-header p {
        color: #A0AEC0;
        margin: 0;
        font-size: 0.9rem;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-title {
        color: #718096;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #2D3748;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 0.3rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2D3748;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        border-bottom: 2px solid #EDF2F7;
        padding-bottom: 0.4rem;
    }
    .stButton>button {
        background-color: #0066F5;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #0052C2;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


# --- DATABASE SETUP & SELF-SEEDING ITEMS ---
def init_db():
  conn = sqlite3.connect("inventory.db", check_same_thread=False)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            opening_stock INTEGER DEFAULT 0
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_in (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            ref_no TEXT,
            item_id TEXT,
            quantity INTEGER,
            note TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            invoice_no TEXT,
            item_id TEXT,
            quantity_sold INTEGER,
            customer TEXT
        )
    """)
  conn.commit()

  # Seed default motor parts catalog if empty (No Excel needed!)
  cursor.execute("SELECT COUNT(*) FROM items")
  if cursor.fetchone()[0] == 0:
    default_parts = [
        ("MP-001", "V-Belt Standard", 0),
        ("MP-002", "Heavy Duty Bearing", 0),
        ("MP-003", "Brake Pad Set", 0),
        ("MP-004", "Oil Filter Premium", 0),
        ("MP-005", "Spark Plug Platinum", 0),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO items (item_id, item_name, opening_stock) VALUES"
        " (?, ?, ?)",
        default_parts,
    )
    conn.commit()

  return conn


conn = init_db()

# --- ZOHO APP HEADER ---
st.markdown("""
    <div class="zoho-header">
        <div>
            <h1>⚙️ Zoho-Style Inventory Management Suite</h1>
            <p>Automated Motor Parts Stock & Sales Operations</p>
        </div>
        <div>
            <span style="background: #2D3748; padding: 6px 12px; border-radius: 4px; font-size: 0.85rem; color: #E2E8F0;">🟢 Live Database Connected</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- FETCH DATA & AGGREGATE VALUES CORRECTLY ---
df_items = pd.read_sql("SELECT item_id, item_name, opening_stock FROM items", conn)
df_stock_in = pd.read_sql("SELECT item_id, quantity FROM stock_in", conn)
df_sales = pd.read_sql("SELECT item_id, quantity_sold FROM sales", conn)

stock_in_grouped = (
    df_stock_in.groupby("item_id")["quantity"].sum().reset_index()
    if not df_stock_in.empty
    else pd.DataFrame(columns=["item_id", "quantity"])
)
sales_grouped = (
    df_sales.groupby("item_id")["quantity_sold"].sum().reset_index()
    if not df_sales.empty
    else pd.DataFrame(columns=["item_id", "quantity_sold"])
)

df_dash = pd.merge(df_items, stock_in_grouped, on="item_id", how="left").fillna(
    0
)
df_dash = pd.merge(df_dash, sales_grouped, on="item_id", how="left").fillna(0)
df_dash.rename(columns={"quantity": "Total Stock In"}, inplace=True)
df_dash["Current Balance"] = (
    df_dash["opening_stock"] + df_dash["Total Stock In"]
) - df_dash["quantity_sold"]

# --- TOP KPIS (ZOHO METRICS ROW) ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
  st.markdown(
      f"""<div class="metric-card"><div class="metric-title">Total Products</div><div"
      f" class="metric-value">{len(df_items)}</div></div>""",
      unsafe_allow_html=True,
  )
with col_m2:
  st.markdown(
      f"""<div class="metric-card"><div class="metric-title">Total Stock In</div><div"
      f" class="metric-value">{int(df_dash['Total Stock In'].sum())}</div></div>""",
      unsafe_allow_html=True,
  )
with col_m3:
  st.markdown(
      f"""<div class="metric-card"><div class="metric-title">Total Sold</div><div"
      f" class="metric-value">{int(df_dash['quantity_sold'].sum())}</div></div>""",
      unsafe_allow_html=True,
  )
with col_m4:
  st.markdown(
      f"""<div class="metric-card"><div class="metric-title">Net Balance</div><div"
      f" class="metric-value">{int(df_dash['Current Balance'].sum())}</div></div>""",
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# --- TABS FOR MODULES ---
tab_dash, tab_sales, tab_stockin = st.tabs(
    ["📊 Inventory Dashboard", "🛒 Sales Operations", "📦 Stock-In Operations"]
)

items_df = pd.read_sql("SELECT item_id, item_name FROM items", conn)
item_options = [
    f"{row['item_id']} - {row['item_name']}" for _, row in items_df.iterrows()
]

with tab_dash:
  st.markdown(
      '<div class="section-title">Live Inventory Status & Stock Balance</div>',
      unsafe_allow_html=True,
  )
  df_display = df_dash.copy()
  df_display.columns = [
      "Item ID",
      "Item Name",
      "Opening Stock",
      "Total Stock In",
      "Total Sold",
      "Current Balance",
  ]
  st.dataframe(df_display, width="stretch", hide_index=True)

with tab_sales:
  col_s1, col_s2 = st.columns([1, 2])
  with col_s1:
    st.markdown(
        '<div class="section-title">Record New Sale</div>',
        unsafe_allow_html=True,
    )
    with st.form("sale_form_zoho", clear_on_submit=True):
      s_date = st.date_input("Date", value=datetime.today())
      s_invoice = st.text_input("Invoice No (e.g., CH-005)")
      s_item = st.selectbox("Select Part", item_options)
      s_qty = st.number_input("Quantity", min_value=1, step=1, value=1)
      s_customer = st.text_input("Customer Name")
      s_submitted = st.form_submit_button("Confirm Sale")

      if s_submitted:
        if not s_item:
          st.error("❌ Please select a valid item.")
        else:
          item_id = s_item.split(" - ")[0]
          cur = conn.cursor()
          cur.execute(
              "SELECT opening_stock FROM items WHERE item_id = ?", (item_id,)
          )
          opening = cur.fetchone()[0]
          cur.execute(
              "SELECT SUM(quantity) FROM stock_in WHERE item_id = ?", (item_id,)
          )
          extra = cur.fetchone()[0] or 0
          cur.execute(
              "SELECT SUM(quantity_sold) FROM sales WHERE item_id = ?",
              (item_id,),
          )
          sold = cur.fetchone()[0] or 0
          bal = (opening + extra) - sold

          if s_qty > bal:
            st.error(f"❌ Stock Error! Available balance: {bal}")
          else:
            cur.execute(
                """INSERT INTO sales (date, invoice_no, item_id, quantity_sold, customer) 
                           VALUES (?, ?, ?, ?, ?)""",
                (str(s_date), s_invoice, item_id, s_qty, s_customer),
            )
            conn.commit()
            st.success("✅ Sale recorded successfully!")
            st.rerun()

  with col_s2:
    st.markdown(
        '<div class="section-title">Sales History Log</div>',
        unsafe_allow_html=True,
    )
    df_sal_log = (
        pd.merge(
            pd.read_sql("SELECT * FROM sales", conn),
            items_df,
            on="item_id",
            how="left",
        )
        if not pd.read_sql("SELECT * FROM sales", conn).empty
        else pd.DataFrame()
    )
    if not df_sal_log.empty:
      df_sal_log = df_sal_log[
          [
              "date",
              "invoice_no",
              "item_id",
              "item_name",
              "quantity_sold",
              "customer",
          ]
      ]
      df_sal_log.columns = [
          "Date",
          "Invoice",
          "ID",
          "Item Name",
          "Qty",
          "Customer",
      ]
      st.dataframe(df_sal_log, width="stretch", hide_index=True)
    else:
      st.info("No sales recorded yet.")

with tab_stockin:
  col_i1, col_i2 = st.columns([1, 2])
  with col_i1:
    st.markdown(
        '<div class="section-title">Add Incoming Stock</div>',
        unsafe_allow_html=True,
    )
    with st.form("stock_form_zoho", clear_on_submit=True):
      i_date = st.date_input("Date", value=datetime.today(), key="idate")
      i_ref = st.text_input("Challan/Ref No (e.g., IMP-208)", key="iref")
      i_item = st.selectbox("Select Part", item_options, key="iitem")
      i_qty = st.number_input(
          "Quantity Received", min_value=1, step=1, value=1, key="iqty"
      )
      i_note = st.text_input("Supplier/Note", key="inote")
      i_submitted = st.form_submit_button("Record Stock In")

      if i_submitted:
        if not i_item:
          st.error("❌ Please select a valid item.")
        else:
          item_id = i_item.split(" - ")[0]
          cur = conn.cursor()
          cur.execute(
              """INSERT INTO stock_in (date, ref_no, item_id, quantity, note) 
                         VALUES (?, ?, ?, ?, ?)""",
 gelap         (str(i_date), i_ref, item_id, i_qty, i_note),
          )
          conn.commit()
          st.success("✅ Stock added successfully!")
          st.rerun()

  with col_i2:
    st.markdown(
        '<div class="section-title">Stock-In History Log</div>',
        unsafe_allow_html=True,
    )
    df_stk_log = (
        pd.merge(
            pd.read_sql("SELECT * FROM stock_in", conn),
            items_df,
            on="item_id",
            how="left",
        )
        if not pd.read_sql("SELECT * FROM stock_in", conn).empty
        else pd.DataFrame()
    )
    if not df_stk_log.empty:
      df_stk_log = df_stk_log[
          ["date", "ref_no", "item_id", "item_name", "quantity", "note"]
      ]
      df_stk_log.columns = ["Date", "Challan", "ID", "Item Name", "Qty", "Note"]
      st.dataframe(df_stk_log, width="stretch", hide_index=True)
    else:
      st.info("No stock-in records yet.")