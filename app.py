from datetime import datetime
import os
import pandas as pd
import sqlite3
import streamlit as st

# --- PAGE CONFIG & iOS-INSPIRED THEME ---
st.set_page_config(
    page_title="Sabir's Inventory Management",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
    .main {
        background-color: #F2F2F7;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Glassmorphism Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border-right: 1px solid rgba(209, 213, 219, 0.4);
        width: 50vw !important;
        max-width: 320px;
    }

    /* App Header Card */
    .app-header {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        color: #1C1C1E;
        padding: 1.2rem 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        display: flex;
        flex-direction: column;
    }
    @media(min-width: 768px) {
        .app-header {
            flex-direction: row;
            justify-content: space-between;
            align-items: center;
        }
    }
    .app-header h1 {
        color: #1C1C1E;
        font-size: 1.35rem;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    .app-header p {
        color: #8E8E93;
        margin: 0;
        font-size: 0.85rem;
        font-weight: 400;
    }

    /* iOS Metric Cards */
    .metric-card {
        background-color: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .metric-title {
        color: #8E8E93;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .metric-value {
        color: #1C1C1E;
        font-size: 1.45rem;
        font-weight: 700;
        margin-top: 0.2rem;
        letter-spacing: -0.5px;
    }

    /* Section Titles */
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1C1C1E;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
        letter-spacing: -0.2px;
    }

    /* iOS Styled Buttons */
    .stButton>button {
        background-color: #007AFF;
        color: white;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.25);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #0056B3;
        box-shadow: 0 6px 16px rgba(0, 122, 255, 0.35);
    }
    
    input, select, textarea {
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)


# --- DATABASE SETUP & MIGRATION FOR TRANSACTION PRICING ---
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
            unit_cost REAL DEFAULT 0.0,
            note TEXT
        )
    """)
  try:
    cursor.execute("ALTER TABLE stock_in ADD COLUMN unit_cost REAL DEFAULT 0.0")
    conn.commit()
  except sqlite3.OperationalError:
    pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            invoice_no TEXT,
            item_id TEXT,
            quantity_sold INTEGER,
            unit_price REAL DEFAULT 0.0,
            customer TEXT
        )
    """)
  try:
    cursor.execute("ALTER TABLE sales ADD COLUMN unit_price REAL DEFAULT 0.0")
    conn.commit()
  except sqlite3.OperationalError:
    pass

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

# --- APP HEADER ---
st.markdown("""
    <div class="app-header">
        <div>
            <h1>⚙️ Sabir's Inventory Management</h1>
            <p>Modern Stock, Pricing & Sales Suite</p>
        </div>
        <div style="margin-top: 8px;">
            <span style="background: rgba(52, 199, 89, 0.15); color: #248A3D; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">● System Online</span>
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
df_stock_in = pd.read_sql(
    "SELECT item_id, quantity, unit_cost FROM stock_in", conn
)
df_sales = pd.read_sql(
    "SELECT item_id, quantity_sold, unit_price FROM sales", conn
)

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

# --- STREAMLINED MAIN MENU KPIS ---
col_m1, col_m2, col_m3 = st.columns(3)
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

st.markdown("<br>", unsafe_allow_html=True)

items_df = pd.read_sql("SELECT item_id, item_name, price FROM items", conn)
item_options = [
    f"{row['item_id']} - {row['item_name']} (৳{row['price']})"
    for _, row in items_df.iterrows()
]

# --- MODULE ROUTING ---
if app_mode == "📊 Inventory Dashboard":
  st.markdown(
      '<div class="section-title">Live Inventory Status & Stock Balance</div>',
      unsafe_allow_html=True,
  )
  df_display = df_dash[
      [
          "item_id",
          "item_name",
          "opening_stock",
          "Total Stock In",
          "quantity_sold",
          "Current Balance",
      ]
  ].copy()
  df_display.columns = [
      "Item ID",
      "Item Name",
      "Opening Stock",
      "Total Stock In",
      "Total Sold",
      "Current Balance",
  ]
  st.dataframe(df_display, width="stretch", hide_index=True)

elif app_mode == "🛒 Sales Operations":
  col_s1, col_s2 = st.columns([1, 2])
  with col_s1:
    st.markdown(
        '<div class="section-title">Record New Sale</div>',
        unsafe_allow_html=True,
    )
    with st.form("sale_form_ios", clear_on_submit=True):
      s_date = st.date_input("Date", value=datetime.today())
      s_invoice = st.text_input("Invoice No (e.g., CH-005)")
      s_item = st.selectbox("Select Part", item_options)
      s_qty = st.number_input("Quantity", min_value=1, step=1, value=1)

      default_p = 0.0
      if s_item:
        try:
          default_p = float(s_item.split("(৳")[1].replace(")", ""))
        except Exception:
          pass

      s_price = st.number_input(
          "Unit Selling Price (৳)", min_value=0.0, step=10.0, value=default_p
      )
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
                """INSERT INTO sales (date, invoice_no, item_id, quantity_sold, unit_price, customer) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(s_date),
                    s_invoice,
                    item_id,
                    s_qty,
                    s_price,
                    s_customer,
                ),
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
        pd.read_sql(
            "SELECT id, date, invoice_no, item_id, quantity_sold, unit_price,"
            " customer FROM sales",
            conn,
        )
        if not pd.read_sql("SELECT * FROM sales", conn).empty
        else pd.DataFrame()
    )
    if not df_sal_log.empty:
      df_sal_log = pd.merge(df_sal_log, items_df, on="item_id", how="left")
      df_sal_log["Total Amount (৳)"] = (
          df_sal_log["quantity_sold"] * df_sal_log["unit_price"]
      )
      df_sal_log = df_sal_log[
          [
              "date",
              "invoice_no",
              "item_id",
              "item_name",
              "quantity_sold",
              "unit_price",
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
    with st.form("stock_form_ios", clear_on_submit=True):
      i_date = st.date_input("Date", value=datetime.today(), key="idate")
      i_ref = st.text_input("Challan/Ref No (e.g., IMP-208)", key="iref")
      i_item = st.selectbox("Select Part", item_options, key="iitem")
      i_qty = st.number_input(
          "Quantity Received", min_value=1, step=1, value=1, key="iqty"
      )

      default_cost = 0.0
      if i_item:
        try:
          default_cost = float(i_item.split("(৳")[1].replace(")", ""))
        except Exception:
          pass

      i_cost = st.number_input(
          "Unit Purchase Cost (৳)",
          min_value=0.0,
          step=10.0,
          value=default_cost,
          key="icost",
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
              """INSERT INTO stock_in (date, ref_no, item_id, quantity, unit_cost, note) 
                         VALUES (?, ?, ?, ?, ?, ?)""",
              (str(i_date), i_ref, item_id, i_qty, i_cost, i_note),
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
        pd.read_sql(
            "SELECT id, date, ref_no, item_id, quantity, unit_cost, note FROM"
            " stock_in",
            conn,
        )
        if not pd.read_sql("SELECT * FROM stock_in", conn).empty
        else pd.DataFrame()
    )
    if not df_stk_log.empty:
      df_stk_log = pd.merge(df_stk_log, items_df, on="item_id", how="left")
      df_stk_log["Total Cost (৳)"] = (
          df_stk_log["quantity"] * df_stk_log["unit_cost"]
      )
      df_stk_log = df_stk_log[
          [
              "date",
              "ref_no",
              "item_id",
              "item_name",
              "quantity",
              "unit_cost",
              "Total Cost (৳)",
              "note",
          ]
      ]
      df_stk_log.columns = [
          "Date",
          "Challan",
          "ID",
          "Item Name",
          "Qty",
          "Unit Cost",
          "Total Cost (৳)",
          "Note",
      ]
      st.dataframe(df_stk_log, width="stretch", hide_index=True)
    else:
      st.info("No stock-in records yet.")

elif app_mode == "🔐 Admin Panel":
  st.markdown(
      '<div class="section-title">🔐 Restricted Admin Panel (Financials &'
      " Management Suite)</div>",
      unsafe_allow_html=True,
  )

  try:
    correct_admin_pass = st.secrets["ADMIN_PASSWORD"]
  except Exception:
    correct_admin_pass = "admin123"

  admin_pass = st.text_input("Enter Admin Password", type="password")

  if admin_pass == correct_admin_pass:
    st.success("🔓 Admin Authentication Successful")

    # --- CALCULATE FINANCIALS & NET PROFIT ---
    df_sales_calc = pd.read_sql(
        "SELECT quantity_sold, unit_price FROM sales", conn
    )
    total_revenue = (
        (df_sales_calc["quantity_sold"] * df_sales_calc["unit_price"]).sum()
        if not df_sales_calc.empty
        else 0.0
    )

    df_stock_calc = pd.read_sql("SELECT quantity, unit_cost FROM stock_in", conn)
    total_stock_spent = (
        (df_stock_calc["quantity"] * df_stock_calc["unit_cost"]).sum()
        if not df_stock_calc.empty
        else 0.0
    )

    net_profit = total_revenue - total_stock_spent
    total_inv_val = df_dash["Total Value"].sum()

    # Display Financial KPIs in Admin Panel (Revenue, Stock Spent, Profit, Inventory Value)
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
      st.markdown(
          f"""<div class="metric-card"><div class="metric-title">Total Revenue</div><div"
          f" class="metric-value" style="color: #34C759;">৳{total_revenue:,.2f}</div></div>""",
          unsafe_allow_html=True,
      )
    with f_col2:
      st.markdown(
          f"""<div class="metric-card"><div class="metric-title">Stock-In Spent</div><div"
          f" class="metric-value" style="color: #FF9500;">৳{total_stock_spent:,.2f}</div></div>""",
          unsafe_allow_html=True,
      )
    with f_col3:
      profit_color = "#34C759" if net_profit >= 0 else "#FF3B30"
      st.markdown(
          f"""<div class="metric-card"><div class="metric-title">Total"
          f" Profit</div><div class="metric-value" style="color:"
          f" {profit_color};">৳{net_profit:,.2f}</div></div>""",
          unsafe_allow_html=True,
      )
    with f_col4:
      st.markdown(
          f"""<div class="metric-card"><div class="metric-title">Inventory Asset"
          f" Value</div><div class="metric-value" style="color:"
          f" #007AFF;">৳{total_inv_val:,.2f}</div></div>""",
          unsafe_allow_html=True,
      )

    st.markdown("<br>", unsafe_allow_html=True)

    admin_sub_tab1, admin_sub_tab2, admin_sub_tab3, admin_sub_tab4, admin_sub_tab5, admin_sub_tab6, admin_sub_tab7 = st.tabs([
        "📈 Everyday Dashboard",
        "👁️ View Catalog & Pricing",
        "➕ Add Part",
        "✏️ Edit Part",
        "🗑️ Delete Part",
        "📦 Delete Stock-In",
        "🛒 Delete Sale",
    ])

    with admin_sub_tab1:
      st.markdown("### 📅 Everyday Transaction Details & Financial Breakdown")

      raw_stock = pd.read_sql(
          "SELECT date, item_id, quantity, unit_cost FROM stock_in", conn
      )
      raw_sales = pd.read_sql(
          "SELECT date, item_id, quantity_sold, unit_price FROM sales", conn
      )

      if not raw_stock.empty or not raw_sales.empty:
        raw_stock["Total Cost"] = raw_stock["quantity"] * raw_stock["unit_cost"]
        raw_sales["Total Revenue"] = (
            raw_sales["quantity_sold"] * raw_sales["unit_price"]
        )

        daily_stock = (
            raw_stock.groupby("date")
            .agg({"quantity": "sum", "Total Cost": "sum"})
            .reset_index()
            if not raw_stock.empty
            else pd.DataFrame(columns=["date", "quantity", "Total Cost"])
        )
        daily_stock.rename(
            columns={
                "quantity": "Total Stock-In Qty",
                "Total Cost": "Stock-In Spend (৳)",
            },
            inplace=True,
        )

        daily_sales = (
            raw_sales.groupby("date")
            .agg({"quantity_sold": "sum", "Total Revenue": "sum"})
            .reset_index()
            if not raw_sales.empty
            else pd.DataFrame(columns=["date", "quantity_sold", "Total Revenue"])
        )
        daily_sales.rename(
            columns={
                "quantity_sold": "Total Sold Qty",
                "Total Revenue": "Revenue Made (৳)",
            },
            inplace=True,
        )

        daily_summary = pd.merge(
            daily_stock, daily_sales, on="date", how="outer"
        ).fillna(0)
        daily_summary["Daily Profit (৳)"] = (
            daily_summary["Revenue Made (৳)"]
            - daily_summary["Stock-In Spend (৳)"]
        )
        daily_summary = daily_summary.sort_values(by="date", ascending=False)

        st.markdown("#### 📊 Daily Summary & Profit Breakdown")
        st.dataframe(daily_summary, width="stretch", hide_index=True)

        st.markdown("---")
        st.markdown("#### 🔍 Filter Everyday Details by Specific Date")
        all_dates = sorted(
            list(
                set(
                    raw_stock["date"].dropna().tolist()
                    + raw_sales["date"].dropna().tolist()
                )
            ),
            reverse=True,
        )
        if all_dates:
          selected_date = st.selectbox("Select Date", all_dates)

          col_d1, col_d2 = st.columns(2)
          with col_d1:
            st.markdown(f"**📦 Stock-In Entries on {selected_date}**")
            sub_stk = pd.read_sql(
                "SELECT ref_no, item_id, quantity, unit_cost, note FROM"
                " stock_in WHERE date = ?",
                conn,
                params=(selected_date,),
            )
            if not sub_stk.empty:
              sub_stk["Total"] = sub_stk["quantity"] * sub_stk["unit_cost"]
              st.dataframe(sub_stk, width="stretch", hide_index=True)
            else:
              st.info("No stock-in records for this date.")

          with col_d2:
            st.markdown(f"**🛒 Sales Entries on {selected_date}**")
            sub_sal = pd.read_sql(
                "SELECT invoice_no, item_id, quantity_sold, unit_price,"
                " customer FROM sales WHERE date = ?",
                conn,
                params=(selected_date,),
            )
            if not sub_sal.empty:
              sub_sal["Total"] = (
                  sub_sal["quantity_sold"] * sub_sal["unit_price"]
              )
              st.dataframe(sub_sal, width="stretch", hide_index=True)
            else:
              st.info("No sales records for this date.")
        else:
          st.info("No dates available.")
      else:
        st.info("No daily transactions logged yet.")

    with admin_sub_tab2:
      st.markdown("### Complete Inventory Catalog & Unit Prices")
      full_catalog = pd.read_sql(
          "SELECT item_id, item_name, opening_stock, price FROM items", conn
      )
      full_catalog.columns = [
          "Item ID",
          "Item Name",
          "Opening Stock",
          "Unit Price (৳)",
      ]
      st.dataframe(full_catalog, width="stretch", hide_index=True)

    with admin_sub_tab3:
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

    with admin_sub_tab4:
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

    with admin_sub_tab5:
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

    with admin_sub_tab6:
      st.markdown("### Delete Incoming Stock Record")
      df_stock_full = pd.read_sql(
          "SELECT id, date, ref_no, item_id, quantity, unit_cost, note FROM"
          " stock_in",
          conn,
      )
      if not df_stock_full.empty:
        stock_choices = [
            f"ID: {row['id']} | Date: {row['date']} | Ref: {row['ref_no']} | Item: {row['item_id']} | Qty: {row['quantity']} | Cost: ৳{row['unit_cost']}"
            for _, row in df_stock_full.iterrows()
        ]
        selected_stock_del = st.selectbox(
            "Select Stock-In Entry to Remove", stock_choices
        )
        if selected_stock_del:
          stock_row_id = int(
              selected_stock_del.split(" | ")[0].replace("ID: ", "")
          )
          if st.button(
              "Confirm Delete Stock-In Entry",
              type="primary",
              key="del_stk_btn",
          ):
            cur = conn.cursor()
            cur.execute("DELETE FROM stock_in WHERE id = ?", (stock_row_id,))
            conn.commit()
            st.success(
                f"🗑 Stock-In record ID {stock_row_id} deleted successfully!"
            )
            st.rerun()
      else:
        st.info("No stock-in records available to delete.")

    with admin_sub_tab7:
      st.markdown("### Delete Sales Transaction Record")
      df_sales_full = pd.read_sql(
          "SELECT id, date, invoice_no, item_id, quantity_sold, unit_price,"
          " customer FROM sales",
          conn,
      )
      if not df_sales_full.empty:
        sales_choices = [
            f"ID: {row['id']} | Date: {row['date']} | Inv: {row['invoice_no']} | Item: {row['item_id']} | Qty: {row['quantity_sold']} | Price: ৳{row['unit_price']} | Cust: {row['customer']}"
            for _, row in df_sales_full.iterrows()
        ]
        selected_sale_del = st.selectbox(
            "Select Sale Entry to Remove", sales_choices
        )
        if selected_sale_del:
          sale_row_id = int(
              selected_sale_del.split(" | ")[0].replace("ID: ", "")
          )
          if st.button(
              "Confirm Delete Sale Entry", type="primary", key="del_sale_btn"
          ):
            cur = conn.cursor()
            cur.execute("DELETE FROM sales WHERE id = ?", (sale_row_id,))
            conn.commit()
            st.success(
                f"🗑 Sales record ID {sale_row_id} deleted successfully!"
            )
            st.rerun()
      else:
        st.info("No sales records available to delete.")

  elif admin_pass == "":
    st.info(
        "🔒 Please enter the admin password to access financial records &"
        " everyday dashboard."
    )
  else:
    st.error("❌ Incorrect Admin Password.")