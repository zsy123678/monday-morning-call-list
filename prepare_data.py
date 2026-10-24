"""Aggregate Online Retail II (UCI 502 / Kaggle lakshmi25npathi) into small CSVs for the dashboard.

Outputs (committed to the repo, well under 25 MB):
  monthly_revenue.csv  - month x country revenue/orders/active customers
  customer_rfm.csv     - one row per customer: R, F, M, tier, country, top category info
Cleaning decisions (documented in README):
  - Rows without Customer ID are anonymous retail walk-ins: excluded from the
    customer-retention dashboard (they cannot be called).
  - Invoices starting with 'C' are cancellations/returns: excluded from revenue
    and RFM so that returns do not inflate a customer's value.
  - Quantity <= 0 or Price <= 0 rows that are not cancellations are adjustments: excluded.
"""
import pandas as pd
import numpy as np

PATH = r"C:\Users\明\ml4biz\10-24-assignment-4\online_retail_II.xlsx"
OUT = r"C:\Users\明\ml4biz\10-24-assignment-4\retention-dashboard"

# --- load both year sheets -------------------------------------------------
dfs = []
xl = pd.ExcelFile(PATH)
print("sheets:", xl.sheet_names)
for sheet in xl.sheet_names:
    d = xl.parse(sheet)
    d["sheet"] = sheet
    dfs.append(d)
df = pd.concat(dfs, ignore_index=True)
df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]
print("raw shape:", df.shape)
print(df.dtypes)

# --- clean ------------------------------------------------------------------
df["invoice"] = df["invoice"].astype(str)
is_cancel = df["invoice"].str.startswith("C")
n_missing_cust = df["customer_id"].isna().sum()
n_cancel = int(is_cancel.sum())

sales = df[~is_cancel].copy()
sales = sales[(sales["quantity"] > 0) & (sales["price"] > 0)]
sales = sales.dropna(subset=["customer_id"])
sales["customer_id"] = sales["customer_id"].astype(int)
sales["revenue"] = sales["quantity"] * sales["price"]
sales["invoicedate"] = pd.to_datetime(sales["invoicedate"])
sales["month"] = sales["invoicedate"].dt.to_period("M").astype(str)
print("clean sales rows:", sales.shape,
      f"| dropped: {n_missing_cust} no-customer-id, {n_cancel} cancellations")

# --- monthly revenue by country ----------------------------------------------
monthly = (sales.groupby(["month", "country"], as_index=False)
           .agg(revenue=("revenue", "sum"),
                orders=("invoice", "nunique"),
                active_customers=("customer_id", "nunique")))
monthly["revenue"] = monthly["revenue"].round(2)
monthly.to_csv(f"{OUT}\\monthly_revenue.csv", index=False)

# --- customer-level RFM (as of snapshot end) -----------------------------------
SNAPSHOT = sales["invoicedate"].max() + pd.Timedelta(days=1)
cust_country = (sales.groupby("customer_id")["country"]
                .agg(lambda s: s.mode().iat[0]))
rfm = sales.groupby("customer_id").agg(
    last_order=("invoicedate", "max"),
    first_order=("invoicedate", "min"),
    frequency=("invoice", "nunique"),
    monetary=("revenue", "sum"),
).reset_index()
rfm["recency_days"] = (SNAPSHOT - rfm["last_order"]).dt.days
rfm["country"] = rfm["customer_id"].map(cust_country)
rfm["monetary"] = rfm["monetary"].round(2)

# A/B/C tiers by monetary value (top 10% = A, next 20% = B, rest = C)
q90 = rfm["monetary"].quantile(0.90)
q70 = rfm["monetary"].quantile(0.70)
rfm["tier"] = np.where(rfm["monetary"] >= q90, "A",
              np.where(rfm["monetary"] >= q70, "B", "C"))
rfm["last_order"] = rfm["last_order"].dt.date
rfm["first_order"] = rfm["first_order"].dt.date
rfm.to_csv(f"{OUT}\\customer_rfm.csv", index=False)

# --- summary for EDA/README -----------------------------------------------------
print("\n=== summary ===")
print("period:", sales["invoicedate"].min(), "->", sales["invoicedate"].max())
print("customers:", rfm.shape[0], "| countries:", sales['country'].nunique())
print("total revenue:", round(sales['revenue'].sum(), 2))
print("tier counts:", rfm['tier'].value_counts().to_dict())
a_silent = rfm[(rfm['tier'] == 'A') & (rfm['recency_days'] > 60)]
ab_silent = rfm[(rfm['tier'].isin(['A', 'B'])) & (rfm['recency_days'] > 60)]
print("A-tier silent>60d:", len(a_silent), "| A/B silent>60d:", len(ab_silent))
print("A-tier monetary share:",
      round(rfm.loc[rfm['tier'] == 'A', 'monetary'].sum() / rfm['monetary'].sum(), 3))
m = sales.groupby("month")["revenue"].sum()
print("\nmonthly revenue:\n", m.round(0))
import os
for f in ["monthly_revenue.csv", "customer_rfm.csv"]:
    p = f"{OUT}\\{f}"
    print(f, round(os.path.getsize(p) / 1e6, 2), "MB")
