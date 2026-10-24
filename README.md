# Monday Morning Call List

**Team: zhangshuyu-team** — a Streamlit dashboard for the key-account retention manager of a UK online gift wholesaler.

- **Live app:** https://monday-morning-call-list.streamlit.app/
- **Repository:** https://github.com/zsy123678/monday-morning-call-list
- **Dataset:** [Online Retail II — Kaggle](https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset) (real transactions, originally published by Dr Daqing Chen, London South Bank University; UCI dataset #502)

---

## Step 1 — The dataset and the decision-maker

**What the data is.** Two years of real transactions (Dec 2009 – 9 Dec 2011) from a UK-based online wholesaler of all-occasion gifts. Most customers are wholesalers themselves — small retailers stocking up. One row is one line item on an invoice: invoice number, stock code, description, quantity, date/time, unit price, customer ID, country. About 1.07M raw rows.

**Who the dashboard is for.** The **key-account retention manager** — one person, whose job is keeping valuable wholesale accounts from quietly drifting away. Not the CEO, not "everyone": the person who owns a phone and a list of accounts.

## Step 2 — Why a dashboard

1. **Who looks at it, and how often?** The retention manager, every Monday morning, before starting the week's calls.
2. **The decision:** *If the retention manager sees an A-tier customer (top 10% by lifetime spend) who has not ordered in over 60 days, they call that customer this week.* The page's bottom table is literally a call list, sorted so the most valuable silent customer is on top.
3. **What do they do today?** Nothing systematic. With ~5,900 identified customers, nobody can remember who last ordered when. Today the company finds out an account was lost months after the fact, when a reorder never arrives. In this data the top 10% of customers hold **64% of all revenue** — an unnoticed defection there is expensive.
4. **Why a dashboard, not a weekly email or an alert?** A weekly email rots in an inbox and cannot be filtered to the manager's own markets; a static report is stale the day it is printed; a pure alert system would fire without context — the manager also needs to see whether the business as a whole is healthy this month, and how the silent-customer pool is trending, before deciding how aggressive to be. The dashboard puts the list, the context, and the filters in one place, in the order they are needed.

## Step 3 — What is on the page, and why

**Top — headline numbers (the "is anything wrong?" row):**

- **Customers who need a call today** — the count of A/B-tier customers past the silence threshold. The single number the manager came for.
- **Revenue, last full month** (with month-over-month delta) — context: is the business healthy while we make these calls?
- **Revenue share held by A-tier customers** — the reminder of what is at stake: 64% of revenue sits in 588 accounts.

**Middle — two charts that explain the numbers:**

- **Monthly revenue trend.** Explains the revenue KPI and shows the wholesale calendar: peaks come in **October–November**, not December, because retailers stock up *before* Christmas. December 2011 is shaded and captioned — it holds only 9 days of data and would otherwise look like a catastrophic crash.
- **Days-since-last-order distribution of A/B customers**, with the call threshold as a red line. Explains the call-list KPI: everyone right of the line is drifting away, and the shape of the distribution tells the manager whether this week's list is unusually long.

**Bottom — the call list itself:** customer ID, country, tier, lifetime spend, order count, last order date, days silent — sorted by lifetime spend, most valuable first. This is the table the manager actually works through.

**Filters (only the ones that get used):** country (the manager owns specific export markets), tier (A/B/C), and the silence threshold (30–180 days, default 60). Nothing else — no date-range pickers or product dropdowns that nobody would touch.

**Two things we chose not to show:**

1. **A country map.** 41 countries look impressive on a map, but no call decision changes by looking at geography in the abstract — the country *filter* does the real work.
2. **A product ranking.** 4,000+ stock codes make a fun chart, but the manager calls *customers*, not products. What a customer bought last matters during the call, not in the queue.

**What could mislead the viewer, and how we handle it:**

- **~23% of invoice lines have no customer ID** (anonymous retail walk-ins). They cannot be called, so they are excluded from every customer metric; leaving them in would overstate the identifiable customer base. Stated in the app's honesty box.
- **Cancellations** (invoices starting with `C`, negative quantities) are excluded from revenue and customer value — otherwise returns inflate both.
- **Partial final month:** December 2011 contains 9 trading days. It is shaded grey on the chart with a caption, and excluded from the "last full month" KPI.
- **Wholesale outliers make means lie.** Individual orders range from 2 units to tens of thousands, so the page reports totals and counts rather than average order value.

**Page order** follows importance: the number that says whether today is a normal Monday, the charts that explain it, and finally the list to work through. A manager who never scrolls still leaves with the answer.

## Step 4 — Refresh frequency

- **Data refresh: nightly.** New invoices arrive every working day, and a customer's "days silent" counter ticks up daily — but nothing on this page moves faster than that, so intraday refresh would add cost without changing any decision.
- **Review cadence: every Monday morning.** Calling is a weekly planning activity; the manager blocks Monday for it. Nightly refresh with weekly review is deliberate — the data must be fresh *when* the review happens, not continuously.
- **What triggers action:** the count of A-tier customers past **60 days** of silence. The 60-day line was chosen from the data: A-tier customers order far more often than that, so 60 quiet days is a genuine anomaly, not normal cadence. If the Monday count jumps sharply (say, more than 20% week over week), that is not a calling problem anymore — something upstream (pricing, stock, service) is broken, and it goes to the sales director.
- **Cost of stale data:** one week stale means roughly a week of newly-silent A-tier accounts missing from the list — accounts holding 64% of revenue discovered late. A month stale and the page is a history lesson: the people on the list may already have signed with a competitor.

## How the data was prepared

The original Kaggle file is a 45 MB Excel workbook (two sheets, one per year), over GitHub's comfort zone. We cleaned and aggregated it in `prepare_data.py` (kept in this repo for transparency):

- dropped rows without a customer ID (anonymous walk-ins, ~23% of lines);
- dropped cancellation invoices (prefix `C`) and non-positive quantity/price adjustment lines;
- aggregated to two small tables: `monthly_revenue.csv` (month × country) and `customer_rfm.csv` (one row per identified customer: recency, frequency, lifetime spend, A/B/C tier by spend decile).

Total committed data: well under 1 MB. `eda.ipynb` shows the exploration behind these decisions.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Repository contents

| File | Purpose |
|---|---|
| `app.py` | the Streamlit dashboard |
| `monthly_revenue.csv`, `customer_rfm.csv` | aggregated data the app reads |
| `prepare_data.py` | how the 45 MB Excel became those two CSVs |
| `eda.ipynb` | the exploration behind the design decisions |
| `requirements.txt` | dependencies |
