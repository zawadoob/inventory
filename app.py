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


# --- DATABASE SETUP & MIGRATION FOR PRICING ---
def init_db():
  conn = sqlite3.connect("inventory.db", check_same_thread=False)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            opening_stock INTEGER DEFAULT 0,
            price REAL DEFAULT 0.0
        )
    """)

  try:
    cursor.execute("ALTER TABLE items ADD COLUMN price REAL DEFAULT 0.0")
    conn.commit()
  except sqlite3.OperationalError:
    pass

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

  cursor.execute("SELECT COUNT(*) FROM items")
  if cursor.fetchone()[0] == 0:
    default_parts = [
        ("MP-001", "V-Belt Standard", 0, 450.0),
        ("MP-002", "Heavy Duty Bearing", 0, 1200.0),
        ("MP-003", "Brake Pad Set", 0, 2500.0),
        ("MP-004", "Oil Filter Premium", 0, 350.0),
        ("MP-005", "Spark Plug Platinum", 0, 600.0),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO items (item_id, item_name, opening_stock, price)"
        " VALUES (?, ?, ?, ?)",
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
            <p>Automated Motor Parts Stock, Pricing & Sales Operations</p>
        </div>
        <div>
            <span style="background: #2D3748; padding: 6px 12px; border-radius: 4px; font-size: 0.85rem; color: #E2E8F0;">🟢 Live Database Connected</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("## 🧭 Navigation")
app_mode = st.sidebar.radio(
    "Choose Module", [
        "📊 Inventory Dashboard",
        "🛒 Sales Operations",
        "📦 Stock-In Operations",
        "🔐 Admin Panel",
    ]
)

# --- FETCH DATA & AGGREGATE VALUES CORRECTLY ---
df_items = pd.read_sql(
    "SELECT item_id, item_name, opening_stock, price FROM items", conn
)
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
df_dash["Total Value"] = df_dash["Current Balance"] * df_dash["price"]

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
      f"""<div class="metric-card"><div class="metric-title">Inventory Value</div><div"
      f" class="metric-value">৳{df_dash['Total Value'].sum():,.2f}</div></div>""",
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

items_df = pd.read_sql("SELECT item_id, item_name, price FROM items", conn)
item_options = [
    f"{row['item_id']} - {row['item_name']} (৳{row['price']})"
    for _, row in items_df.iterrows()
]

# --- MODULE ROUTING ---
if app_mode == "📊 Inventory Dashboard":
  st.markdown(
      '<div class="section-title">Live Inventory Status, Stock Balance &'
      " Pricing</div>",
      unsafe_allow_html=True,
  )
  df_display = df_dash[
      [
          "item_id",
          "item_name",
          "price",
          "opening_stock",
          "Total Stock In",
          "quantity_sold",
          "Current Balance",
          "Total Value",
      ]
  ].copy()
  df_display.columns = [
      "Item ID",
      "Item Name",
      "Unit Price (৳)",
      "Opening Stock",
      "Total Stock In",
      "Total Sold",
      "Current Balance",
      "Total Stock Value (৳)",
  ]
  st.dataframe(df_display, width="stretch", hide_index=True)

elif app_mode == "🛒 Sales Operations":
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
      df_sal_log["Total Amount (৳)"] = (
          df_sal_log["quantity_sold"] * df_sal_log["price"]
      )
      df_sal_log = df_sal_log[
          [
              "date",
              "invoice_no",
              "item_id",
              "item_name",
              "quantity_sold",
              "price",
              "Total Amount (৳)",
              "customer",
          ]
      ]
      df_sal_log.columns = [
          "Date",
          "Invoice",
          "ID",
          "Item Name",
          "Qty",
          "Unit Price",
          "Total (৳)",
          "Customer",
      ]
      st.dataframe(df_sal_log, width="stretch", hide_index=True)
    else:
      st.info("No sales recorded yet.")

elif app_mode == "📦 Stock-In Operations":
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
              (str(i_date), i_ref, item_id, i_qty, i_note),
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

elif app_mode == "🔐 Admin Panel":
  st.markdown(
      '<div class="section-title">🔐 Restricted Admin Panel (Full Management'
      " Suite)</div>",
      unsafe_allow_html=True,
  )

  try:
    correct_admin_pass = st.secrets["ADMIN_PASSWORD"]
  except Exception:
    correct_admin_pass = "admin123"

  admin_pass = st.text_input("Enter Admin Password", type="password")

  if admin_pass == correct_admin_pass:
    st.success("🔓 Admin Authentication Successful")

    admin_sub_tab1, admin_sub_tab2, admin_sub_tab3, admin_sub_tab4, admin_sub_tab5, admin_sub_tab6 = st.tabs([
        "👁️ View Catalog",
        "➕ Add Part",
        "✏️️ Edit Part",
        "🗑️ Delete Part",
        "📦 Delete Stock-In",
        "🛒 Delete Sale",
    ])

    with admin_sub_tab1:
      st.markdown("### Complete Inventory Catalog")
      full_catalog = pd.read_sql("SELECT * FROM items", conn)
      full_catalog.columns = ["Item ID", "Item Name", "Opening Stock", "Unit Price (৳)"]
      st.dataframe(full_catalog, width="stretch", hide_index=True)

    with admin_sub_tab2:
      st.markdown("### Create New Part")
      with st.form("create_part_form"):
        new_id = st.text_input("Item ID (e.g., MP-006)")
        new_name = st.text_input("Item Name (e.g., Alternator Belt)")
        new_opening = st.number_input(
            "Initial Opening Stock", min_value=0, step=1, value=0
        )
        new_price = st.number_input(
            "Unit Price (৳)", min_value=0.0, step=10.0, value=100.0
        )
        create_submitted = st.form_submit_button("Create Part")

        if create_submitted:
          if not new_id or not new_name:
            st.error("❌ Item ID and Name are required.")
          else:
            try:
              cur = conn.cursor()
              cur.execute(
                  """INSERT INTO items (item_id, item_name, opening_stock, price) 
                             VALUES (?, ?, ?, ?)""",
                  (new_id.strip(), new_name.strip(), new_opening, new_price),
              )
              conn.commit()
              st.success(f"✅ Successfully created item {new_id} - {new_name}!")
              st.rerun()
            except sqlite3.IntegrityError:
              st.error(
                  f"❌ Error: Item ID '{new_id}' already exists in the catalog!"
              )

    with admin_sub_tab3:
      st.markdown("### Update Existing Part Details & Price")
      edit_item_select = st.selectbox(
          "Select Item to Edit", item_options, key="edit_select"
      )
      if edit_item_select:
        selected_id = edit_item_select.split(" - ")[0]
        cur = conn.cursor()
        cur.execute(
            "SELECT item_name, opening_stock, price FROM items WHERE item_id = ?",
            (selected_id,),
        )
        curr_name, curr_stock, curr_price = cur.fetchone()

        with st.form("update_part_form"):
          u_name = st.text_input("Item Name", value=curr_name)
          u_stock = st.number_input(
              "Opening Stock", value=curr_stock, min_value=0, step=1
          )
          u_price = st.number_input(
              "Unit Price (৳)", value=float(curr_price), min_value=0.0, step=10.0
          )
          update_submitted = st.form_submit_button("Update Item")

          if update_submitted:
            cur.execute(
                """UPDATE items SET item_name = ?, opening_stock = ?, price = ? 
                           WHERE item_id = ?""",
                (u_name, u_stock, u_price, selected_id),
            )
            conn.commit()
            st.success(f"✅ Successfully updated item {selected_id}!")
            st.rerun()

    with admin_sub_tab4:
      st.markdown("### Delete Item from Catalog")
      del_item_select = st.selectbox(
          "Select Item to Delete", item_options, key="del_select"
      )
      if del_item_select:
        del_id = del_item_select.split(" - ")[0]
        st.warning(
            f"⚠ Warning: Deleting item `{del_id}` will permanently remove it"
            " from the database catalog."
        )
        if st.button("Confirm and Delete Item", type="primary"):
          cur = conn.cursor()
          cur.execute("DELETE FROM items WHERE item_id = ?", (del_id,))
          conn.commit()
          st.success(f"🗑 Item {del_id} deleted successfully!")
          st.rerun()

    with admin_sub_tab5:
      st.markdown("### Delete Incoming Stock Record")
      df_stock_full = pd.read_sql(
          "SELECT id, date, ref_no, item_id, quantity, note FROM stock_in", conn
      )
      if not df_stock_full.empty:
        stock_choices = [
            f"ID: {row['id']} | Date: {row['date']} | Ref: {row['ref_no']} | Item: {row['item_id']} | Qty: {row['quantity']}"
            for _, row in df_stock_full.iterrows()
        ]
        selected_stock_del = st.selectbox(
            "Select Stock-In Entry to Remove", stock_choices
        )
        if selected_stock_del:
          stock_row_id = int(selected_stock_del.split(" | ")[0].replace("ID: ", ""))
          if st.button("Confirm Delete Stock-In Entry", type="primary", key="del_stk_btn"):
            cur = conn.cursor()
            cur.execute("DELETE FROM stock_in WHERE id = ?", (stock_row_id,))
            conn.commit()
            st.success(f"🗑 Stock-In record ID {stock_row_id} deleted successfully!")
            st.rerun()
      else:
        st.info("No stock-in records available to delete.")

    with admin_sub_tab6:
      st.markdown("### Delete Sales Transaction Record")
      df_sales_full = pd.read_sql(
          "SELECT id, date, invoice_no, item_id, quantity_sold, customer FROM sales", conn
      )
      if not df_sales_full.empty:
        sales_choices = [
            f"ID: {row['id']} | Date: {row['date']} | Inv: {row['invoice_no']} | Item: {row['item_id']} | Qty: {row['quantity_sold']} | Cust: {row['customer']}"
            for _, row in df_sales_full.iterrows()
        ]
        selected_sale_del = st.selectbox(
            "Select Sale Entry to Remove", sales_choices
        )
        if selected_sale_del:
          sale_row_id = int(selected_sale_del.split(" | ")[0].replace("ID: ", ""))
          if st.button("Confirm Delete Sale Entry", type="primary", key="del_sale_btn"):
            cur = conn.cursor()
            cur.execute("DELETE FROM sales WHERE id = ?", (sale_row_id,))
            conn.commit()
            st.success(f"🗑 Sales record ID {sale_row_id} deleted successfully!")
            st.rerun()
      else:
        st.info("No sales records available to delete.")

  elif admin_pass == "":
    st.info("🔒 Please enter the admin password to access CRUD controls.")
  else:
    st.error("❌ Incorrect Admin Password.")