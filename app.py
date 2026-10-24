"""
Monday Morning Call List — a retention dashboard for a wholesale gift company.
Dataset: Online Retail II (Kaggle: lakshmi25npathi/online-retail-dataset),
real transactions of a UK-based online gift wholesaler, Dec 2009 - 9 Dec 2011.
"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

TEAM_NAME = "zhangshuyu-team"
CALL_THRESHOLD_DEFAULT = 60  # days of silence before an A/B customer needs a call

st.set_page_config(page_title="Monday Morning Call List", layout="wide")

# ---------------------------------------------------------------- data ------
@st.cache_data
def load_data():
    monthly = pd.read_csv("monthly_revenue.csv", parse_dates=["month"])
    rfm = pd.read_csv("customer_rfm.csv", parse_dates=["last_order", "first_order"])
    return monthly, rfm


monthly, rfm = load_data()

# --------------------------------------------------------------- header -----
st.title(f"Monday Morning Call List — {TEAM_NAME}")
st.caption(
    "For the **key-account retention manager** of a UK gift wholesaler. "
    "It answers one question every Monday: **which valuable customers have gone quiet — whose call cannot wait?**"
)
st.caption(
    "Data: Dec 2009 – 9 Dec 2011 (Kaggle snapshot, Online Retail II). "
    "In production: order data would refresh **nightly**; the manager reviews this page **every Monday morning**; "
    "an alert fires the same day an A-tier customer passes the silence threshold."
)

# -------------------------------------------------------------- filters -----
with st.sidebar:
    st.header("Filters")
    countries = ["All countries"] + sorted(rfm["country"].unique().tolist())
    country = st.selectbox(
        "Customer country", countries,
        help="The manager owns specific export markets; this is the filter they actually use.")
    tiers = st.multiselect("Customer tier", ["A", "B", "C"], default=["A", "B"],
                           help="A = top 10% by lifetime spend, B = next 20%. C-tier customers are not called.")
    threshold = st.slider("Call threshold (days since last order)", 30, 180,
                          CALL_THRESHOLD_DEFAULT, step=15)

mask = rfm["tier"].isin(tiers)
monthly_view = monthly
if country != "All countries":
    mask &= rfm["country"] == country
    monthly_view = monthly[monthly["country"] == country]
view = rfm[mask]

# ------------------------------------------------------------ headline KPIs -
# monthly_revenue.csv holds one row per month x country — aggregate first.
# December 2011 holds only 9 days of data — exclude it from the "current month" KPI.
m_by_month = monthly_view.groupby("month")["revenue"].sum().sort_index()
full = m_by_month[m_by_month.index < "2011-12-01"]
last, prev = full.iloc[-1], full.iloc[-2]
mom_delta = (last - prev) / prev

call_list = view[view["recency_days"] > threshold].sort_values("monetary", ascending=False)
tier_a_share = rfm.loc[rfm["tier"] == "A", "monetary"].sum() / rfm["monetary"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Customers who need a call today", f"{len(call_list)}",
          help=f"Tier {tiers} customers silent more than {threshold} days, sorted by lifetime spend below.")
c2.metric("Revenue — last full month (Nov 2011)", f"£{last:,.0f}",
          f"{mom_delta:+.1%} vs Oct 2011")
c3.metric("Revenue held by A-tier customers", f"{tier_a_share:.0%}",
          help="588 customers — the top 10% — hold this share of all revenue. Losing them is the real risk.")

st.divider()

# ------------------------------------------------------- supporting charts --
left, right = st.columns(2)

with left:
    st.subheader("Why the season matters: monthly revenue")
    fig, ax = plt.subplots(figsize=(7, 3.6))
    m = m_by_month
    ax.plot(m.index, m.values, marker="o", color="#1f77b4")
    ax.axvspan(pd.Timestamp("2011-12-01"), m.index.max(), color="grey", alpha=0.2)
    ax.annotate("partial month\n(9 days only)", xy=(pd.Timestamp("2011-12-04"), m.iloc[-1]),
                xytext=(-90, 30), textcoords="offset points", fontsize=8, color="dimgray",
                arrowprops=dict(arrowstyle="->", color="dimgray"))
    ax.set_ylabel("Revenue (£)")
    ax.set_title("Peaks arrive in Oct–Nov: retailers stock up before Christmas",
                 fontsize=10, color="dimgray")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)
    st.caption("December 2011 looks like a crash but contains only 9 trading days — "
               "the grey shading marks it so nobody misreads the trend.")

with right:
    st.subheader("Why the list grows: silence of valuable customers")
    fig2, ax2 = plt.subplots(figsize=(7, 3.6))
    data = view[view["tier"].isin(["A", "B"])]["recency_days"]
    ax2.hist(data, bins=30, color="#1f77b4")
    ax2.axvline(threshold, color="red", ls="--", label=f"call threshold: {threshold} days")
    ax2.set_xlabel("Days since last order")
    ax2.set_ylabel("Customers")
    ax2.legend()
    ax2.set_title("Every customer right of the red line is drifting away", fontsize=10, color="dimgray")
    st.pyplot(fig2)

# ------------------------------------------------------------- call list ----
st.subheader(f"The call list — {len(call_list)} customers, most valuable first")
st.caption("Work it top to bottom. A-tier first: the top of this table is where the revenue lives.")
show = call_list[["customer_id", "country", "tier", "monetary", "frequency",
                  "last_order", "recency_days"]].rename(columns={
    "customer_id": "Customer ID", "country": "Country", "tier": "Tier",
    "monetary": "Lifetime spend (£)", "frequency": "Orders",
    "last_order": "Last order", "recency_days": "Days silent"})
st.dataframe(show.style.format({"Lifetime spend (£)": "£{:,.0f}"}),
             width="stretch", hide_index=True)

# --------------------------------------------------- honesty about the data -
with st.expander("What this dashboard deliberately does not show — and what could mislead you"):
    st.markdown(
        "- **No country map, no product ranking.** 41 countries and 4,000+ products are interesting, "
        "but neither changes *who to call today*; the country filter above is enough.\n"
        "- **Anonymous walk-ins are excluded.** ~23% of invoice lines have no customer ID. They count in "
        "revenue but cannot be called, so they are out of the customer metrics — mixing them in would "
        "overstate the identifiable customer base.\n"
        "- **Returns are excluded.** Cancellations (invoices starting with 'C') carry negative quantities; "
        "counted as sales they would inflate both revenue and a customer's value.\n"
        "- **Averages would lie here.** Wholesale orders range from a few units to tens of thousands, so "
        "this page reports totals and counts rather than average order values."
    )
