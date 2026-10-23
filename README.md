# Niamito business workspace

A Streamlit workspace for primary sales, consumer sell-out, marketing, profitability and product performance.

## Run

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Existing Streamlit deployments pointing at `appreal.py` continue to work. Both entry points now use the same workbook loader and dashboard. The prior demo-oriented `app.py` is preserved as `legacy_app.py` and can still be run explicitly.

The app loads `Niamito_Master_Tables.xlsx` from the repository. An uploaded workbook overrides it for the current session only. This is a workbook snapshot, not a live Google Sheets connection. Replacing the workbook invalidates the content-based cache. An unreadable upload shows an error instead of silently switching to demonstration data.

## Views

- **Overview:** primary and consumer units lead the KPIs and trends, followed by the retained revenue charts, a photographed product-family shelf, market results and source coverage. Five switchable perspectives explore product families, flavours, markets, retailers and marketing mix. Primary and secondary figures are never added together.
- **Sales:** the existing primary/secondary breakdowns, market navigation, volume/revenue switch, year-over-year comparisons, annual goal and all six forecast methods with scenarios.
- **Marketing:** all charts and tables stay together in one scrolling view: recorded product allocations, monthly reconciliation, calendar trends, original monthly/cumulative spend, annotated channel spend/counts, ATL/BTL and supporting costs, product/retailer matrix, units-versus-spend and revenue context, influencer records, both source and expanded expense registers, search, exports and source-quality actions.
- **Profitability:** the existing 2026 annual expense model and waterfall, with its annual cost and market-allocation limitations stated explicitly.
- **Products:** a UHT/HPP product shelf with real Niamito product photography and period-filtered performance, plus the existing SKU comparisons, trends, ranking and market views. Historical products remain in detailed tables.
- **Data & exports:** typed records, CSV downloads and reporting definitions.

## Marketing sources and interpretation

The two marketing sources overlap. Do not sum them:

1. **Expenses / Marketing & Promo:** the workbook's existing 2026 product allocation model. Monthly allocations are summed once per product family. Partial date selections include the whole allocation month. Calendar classification filters do not change this model.
2. **Marketing Calendar:** one detailed expense per row. The first `TOTAL Spend (€)` column is authoritative in the current workbook. Blank-name total rows are excluded. Duplicate-looking expense rows are flagged but retained for invoice reconciliation.

In the current source, allocations contain non-zero amounts through August 2026, while calendar detail ends in June. The reconciliation table exposes missing detail and rounding differences rather than assuming missing records mean zero spend.

Optional calendar columns `Product Family` (or `Product Line`), `Segment`, `Retailer` (or `Store`) take priority over name-based classification. Existing `Market` values take priority over country clues in expense names. Unassigned/shared costs are never copied into several groups. Each exported row includes the classification basis and original Excel row. The standardized channel and original source type remain available.

Optional `Attributed Revenue (€)` enables reported ROAS only for records with attributed revenue and positive spend. Missing attribution stays missing, including a distinction between a recorded zero and no value. Sales/spend charts show context; they do not claim marketing caused the sales.

## Verification

```bash
python -m unittest discover -s tests -v
```

Regression checks cover the repository workbook totals, September returns and revenue-only adjustments, marketing-total exclusion, complete reconciliation across dimensions, 2026 product allocations, month boundaries, safe CSV exports, both deployment entry points and interactive filters. UI checks exercise all six forecast methods, scenarios, revenue mode, category selection, empty results and custom date ranges.

The workbook itself is unchanged by the redesign. Accounting allocation rules and forecast assumptions are retained rather than silently replaced.

## Niamito identity and product imagery

The dashboard uses Niamito's chocolate/cream/pastel identity, official logo, Right Grotesk web fonts and product photography from the brand's own website. Assets are bundled under `assets/brand` so rendering does not depend on image requests to a third party. `assets/brand/sources.json` records each original URL. The brand owner requested this reuse for its dashboard; any redistribution of these assets must respect the brand's existing rights and font licence.

The oatmeal photograph comes from the supplied Origin record for Blueberry Oat Meal (BLK05-1014). It identifies the Kaša family and Blueberry flavour; Choco and Peach retain typographic placeholders until their own verified photos are supplied. Product images do not imply current stock or availability. Product cards lead with primary units and calculate primary/secondary units and revenue independently from the selected records.

The presentation uses a compact editorial header, restrained Niamito colours and smaller straight product photos. The existing sales, forecast, profitability and product graphs and tables remain accessible in their original main sections. Revenue analyses remain available alongside the units-first emphasis. Marketing sections are sequential rather than hidden in nested tabs.

## Source structure

- `appreal.py`: dashboard orchestration and retained detailed business views.
- `dashboard_data.py`: shared workbook parser and content-keyed caching.
- `dashboard_ui.py`, `dashboard.css`: visual system and export helpers.
- `marketing.py`: marketing normalization, classification, analysis and allocations.
- `overview.py`: executive overview and data explorer.
- `brand.py`, `assets/brand`: bundled brand identity, product-family cards and flavour shelf.
- `perspectives.py`: reconciled product, flavour, market, retailer and marketing views.
