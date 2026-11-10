# Market Demand Dashboard

Explore how demand varies by region, category and month. This public edition of an independent analytics dashboard includes the API, browser interface, database schema, reproducible seed generator and export code. The city names are real. Demand metrics, budgets, events and business insights are synthetic.

## Run locally

Use Python 3.11 or newer. From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Open **http://127.0.0.1:8002** for the dashboard or **http://127.0.0.1:8002/docs** for the API. On first start it creates a local SQLite database with 20 regions, eight service categories and 12 months of demand signals. The browser loads Chart.js from jsDelivr.

## Follow a number

The seed generator writes one row per region, service category and calendar month. The heatmap selects the latest month, filters by category when requested, and groups by region. The overview summarizes the full history. The report endpoint returns a PDF, PowerPoint or Excel workbook.

Run the integration checks in the activated environment:

```sh
python -m unittest -v
```
