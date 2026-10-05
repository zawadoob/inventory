import pandas as pd

# Create a clean, confidential-free Excel template
with pd.ExcelWriter("inventory_template.xlsx", engine="openpyxl") as writer:

  # 1. Inventory Dashboard (Data starts at row index 3 as expected by app.py)
  dash_data = [
      ["Inventory Dashboard", "", "", "", ""],
      ["", "", "", "", ""],
      ["Item ID", "Item Name", "Opening Stock", "Category", "Unit"],
      ["MP-001", "V-Belt Standard", 0, "Belts", "Pcs"],
      ["MP-002", "Heavy Duty Bearing", 0, "Bearings", "Pcs"],
      ["MP-003", "Brake Pad Set", 0, "Brakes", "Set"],
      ["MP-004", "Oil Filter Premium", 0, "Filters", "Pcs"],
      ["MP-005", "Spark Plug Platinum", 0, "Ignition", "Pcs"],
  ]
  pd.DataFrame(dash_data).to_excel(
      writer, sheet_name="Inventory Dashboard", index=False, header=False
  )

  # 2. Stock In Log
  stock_data = [
      ["Stock In Log", "", "", "", "", ""],
      ["", "", "", "", "", ""],
      ["Date", "Ref No", "Item ID", "Quantity", "Note", "Supplier"],
      ["2026-01-01", "INIT", "MP-001", 0, "Template Placeholder", "None"],
  ]
  pd.DataFrame(stock_data).to_excel(
      writer, sheet_name="Stock In Log", index=False, header=False
  )

  # 3. Sales Log
  sales_data = [
      ["Sales Log", "", "", "", "", "", ""],
      ["", "", "", "", "", ""],
      [
          "Date",
          "Invoice No",
          "Item ID",
          "Name",
          "Quantity Sold",
          "Customer",
          "Price",
      ],
      ["2026-01-01", "INIT", "MP-001", "V-Belt Standard", 0, "Template Placeholder", 0],
  ]
  pd.DataFrame(sales_data).to_excel(
      writer, sheet_name="Sales Log", index=False, header=False
  )

print("✅ inventory_template.xlsx created successfully!")