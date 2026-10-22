"""Workbook loading shared by both dashboard entry points."""
import pandas as pd
import numpy as np
import streamlit as st
from datetime import timedelta
from io import BytesIO


@st.cache_data(show_spinner=False)
def load_excel_cached(payload: bytes):
    """Content-keyed cache: replacing the workbook invalidates the cached tables."""
    return load_excel(BytesIO(payload))

BEIGE  = "#EDE3D8"
BROWN  = "#2C1A0E"
LAVEN  = "#9497C4"
GREEN  = "#6BA547"
CORAL  = "#D4663C"
YELLOW = "#C8A84B"
CREAM  = "#F0E8DC"
MID    = "#7A5230"

def hex_alpha(hex_color, alpha):
    """Convert a 6-digit hex color + float alpha to an rgba() string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

MARKET_COLORS = {"SI": BROWN, "HR": LAVEN, "DE": GREEN}
SKU_COLORS    = {
    "NIA-OG-250": BROWN,
    "NIA-VN-250": LAVEN,
    "NIA-CH-250": CORAL,
    "NIA-MP-500": YELLOW,
}

# ──────────────────────────────────────────────────────────────────────────────
# PRODUCT CATEGORIES
# ──────────────────────────────────────────────────────────────────────────────
ALL_CATEGORIES = ["Niamito Oatmeal", "Niamito Fresh Meal", "Niamito Meal in a Bottle"]

_CAT_KEYWORDS = {
    # Oatmeal MUST be checked first — its products also contain "hpp" and flavour words
    # that appear in Fresh Meal keywords, so order matters.
    "Niamito Oatmeal":          ["oatmeal", "oat"],
    "Niamito Meal in a Bottle": ["uht", "470", "cocoa", "cookie", "vanilla", "meal in a bottle"],
    "Niamito Fresh Meal":       ["fresh meal", "fresh", "hpp", "390", "apple", "blueberry",
                                  "spinach", "strawberry", "jaffa", "borovn", "jagod",
                                  "\u0161pina\u010d", "jabolč"],
}

CATEGORY_COLORS = {
    "Niamito Fresh Meal":         GREEN,
    "Niamito Oatmeal":            BROWN,
    "Niamito Meal in a Bottle":   LAVEN,
}

def get_product_category(sku_name: str) -> str:
    """Map a product name to one of three Niamito product categories."""
    name = str(sku_name).lower()
    for cat, keywords in _CAT_KEYWORDS.items():
        if any(k in name for k in keywords):
            return cat
    return "Niamito Fresh Meal"  # safe fallback; Oatmeal is now matched explicitly above


@st.cache_data(show_spinner=False)
def generate_demo_data():
    rng = np.random.default_rng(42)

    PRODUCTS = {
        # Fresh Meal (HPP 390g)
        "APL05": {"name": "Fresh Meal Apple 390g",       "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        "BLU05": {"name": "Fresh Meal Blueberry 390g",   "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        "SPN05": {"name": "Fresh Meal Spinach 390g",     "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        "STR05": {"name": "Fresh Meal Strawberry 390g",  "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        # Oatmeal
        "BLK05": {"name": "Blueberry Oat",               "price": 3.50, "bpc": 1, "line": "Niamito Oatmeal"},
        "CHK05": {"name": "Choco Oat",                   "price": 3.50, "bpc": 1, "line": "Niamito Oatmeal"},
        "PCK05": {"name": "Peach Oat",                   "price": 3.50, "bpc": 1, "line": "Niamito Oatmeal"},
        # Meal in a Bottle (UHT 470ml)
        "COU05-DE": {"name": "Meal in a Bottle Cocoa 470ml",   "price": 3.80, "bpc": 1, "line": "Niamito Meal in a Bottle"},
        "CKU05-DE": {"name": "Meal in a Bottle Cookie 470ml",  "price": 3.80, "bpc": 1, "line": "Niamito Meal in a Bottle"},
        "VAU05-DE": {"name": "Meal in a Bottle Vanilla 470ml", "price": 3.80, "bpc": 1, "line": "Niamito Meal in a Bottle"},
    }

    weeks = pd.date_range("2024-01-01", "2026-04-28", freq="W-MON")

    # Base weekly bottles per SKU per market
    BASE = {
        "SI": {
            "APL05": 120, "BLU05": 95, "SPN05": 60, "STR05": 80,
            "BLK05": 70, "CHK05": 55, "PCK05": 50,
            "COU05-DE": 0, "CKU05-DE": 0, "VAU05-DE": 0,
        },
        "HR": {
            "APL05": 50, "BLU05": 40, "SPN05": 25, "STR05": 35,
            "BLK05": 30, "CHK05": 25, "PCK05": 20,
            "COU05-DE": 0, "CKU05-DE": 0, "VAU05-DE": 0,
        },
        "DE": {
            "APL05": 0, "BLU05": 0, "SPN05": 0, "STR05": 0,
            "BLK05": 0, "CHK05": 0, "PCK05": 0,
            "COU05-DE": 80, "CKU05-DE": 65, "VAU05-DE": 55,
        },
    }

    primary_rows = []
    for i, wk in enumerate(weeks):
        growth = 1 + i * 0.008
        for mkt, sku_dict in BASE.items():
            for sku, base_bottles in sku_dict.items():
                if base_bottles == 0:
                    continue
                bottles = max(1, int(base_bottles * growth * rng.uniform(0.85, 1.18)))
                price = PRODUCTS[sku]["price"]
                gross = round(bottles * price, 2)
                primary_rows.append({
                    "week": wk,
                    "market": mkt,
                    "sku_id": sku,
                    "sku_name": PRODUCTS[sku]["name"],
                    "cases": 0,
                    "bottles": bottles,
                    "list_price": price,
                    "gross_revenue": gross,
                    "trade_discount": 0.0,
                    "net_revenue": gross,
                    "funnel_type": "3-tier" if mkt in ["SI", "HR"] else "2-tier",
                    "category": PRODUCTS[sku]["line"],
                })

    prim_df = pd.DataFrame(primary_rows)
    prim_df["category"] = prim_df["sku_name"].apply(get_product_category)

    # ── Secondary sales (retail sell-out, SI only, no revenue) ────────────────
    RETAILER_POOL = [f"Retailer_{i:03d}" for i in range(1, 224)]
    so_rows = []
    so_weeks = pd.date_range("2025-01-06", "2026-04-28", freq="W-MON")
    si_skus = [k for k, v in PRODUCTS.items() if v["line"] in ("Niamito Fresh Meal", "Niamito Oatmeal")]
    for wk in so_weeks:
        n_retailers = rng.integers(30, 80)
        chosen = rng.choice(RETAILER_POOL, size=n_retailers, replace=False)
        for ret in chosen:
            sku = rng.choice(si_skus)
            units = int(rng.integers(2, 25))
            so_rows.append({
                "week": wk,
                "market": "SI",
                "retailer": ret,
                "sku_id": sku,
                "sku_name": PRODUCTS[sku]["name"],
                "bottles_sold": units,
                "consumer_price": 0.0,
                "sellout_revenue": 0.0,
                "funnel_type": "3-tier",
                "category": PRODUCTS[sku]["line"],
            })
    so_df = pd.DataFrame(so_rows)
    so_df["category"] = so_df["sku_name"].apply(get_product_category)

    # ── Distributor stock (SI & HR) ───────────────────────
    stock_rows = []
    for mkt in ["SI", "HR"]:
        stock = 0
        for wk in weeks:
            c_in = int(prim_df[(prim_df["market"] == mkt) & (prim_df["week"] == wk)]["bottles"].sum() // 12)
            c_out = int(c_in * rng.uniform(0.72, 0.96))
            stock = max(0, stock + c_in - c_out)
            stock_rows.append({
                "week": wk, "market": mkt,
                "cases_in": c_in, "cases_out": c_out,
                "stock_cases": stock,
                "stock_to_sales": round(stock / max(c_out, 1), 2),
            })
    stock_df = pd.DataFrame(stock_rows)

    # ── Marketing Calendar ────────────────────────────────
    mkt_campaigns = [
        {"id": "MKT-2024-001", "name": "Q1 Digital SI",           "channel": "Digital",     "market": "SI",  "start": "2024-01-15", "end": "2024-02-28", "media_spend": 2500, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-002", "name": "Spring Events SI",         "channel": "Events",      "market": "SI",  "start": "2024-03-01", "end": "2024-04-30", "media_spend": 3800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-003", "name": "Mercator Listing Q1",      "channel": "Team",        "market": "SI",  "start": "2024-01-01", "end": "2024-01-01", "media_spend": 0,    "listing_fee": 4500, "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Store",  "window_days": 0},
        {"id": "MKT-2024-004", "name": "Production Campaign",      "channel": "Production",  "market": "SI",  "start": "2024-05-01", "end": "2024-05-31", "media_spend": 1800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-005", "name": "HR Market Launch",         "channel": "Events",      "market": "HR",  "start": "2024-06-01", "end": "2024-06-30", "media_spend": 3200, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-006", "name": "DE Launch Digital",        "channel": "Digital-Intl","market": "DE",  "start": "2024-07-01", "end": "2024-08-31", "media_spend": 5500, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-007", "name": "@healthysi Collab",        "channel": "Digital",     "market": "SI",  "start": "2024-09-10", "end": "2024-09-24", "media_spend": 700,  "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": "@healthysi", "reach": 32000, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-008", "name": "Q4 Traditional SI",        "channel": "Traditional", "market": "SI",  "start": "2024-10-01", "end": "2024-12-31", "media_spend": 4200, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-001", "name": "Jan Digital Push",         "channel": "Digital",     "market": "SI",  "start": "2025-01-15", "end": "2025-02-15", "media_spend": 2800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-002", "name": "Spring Events HR",         "channel": "Events",      "market": "HR",  "start": "2025-03-01", "end": "2025-04-30", "media_spend": 3500, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-003", "name": "@fitnesswelt_de Collab",   "channel": "Digital-Intl","market": "DE",  "start": "2025-04-01", "end": "2025-04-21", "media_spend": 2000, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": "@fitnesswelt_de", "reach": 115000, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-004", "name": "Production 2025",          "channel": "Production",  "market": "SI",  "start": "2025-05-01", "end": "2025-05-31", "media_spend": 2100, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-005", "name": "Konzum Listing HR",        "channel": "Team",        "market": "HR",  "start": "2025-06-01", "end": "2025-06-01", "media_spend": 0,    "listing_fee": 3800, "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Store",  "window_days": 0},
        {"id": "MKT-2025-006", "name": "Q4 Traditional SI",        "channel": "Traditional", "market": "SI",  "start": "2025-10-01", "end": "2025-12-31", "media_spend": 4800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-001", "name": "Q1 Digital 2026",          "channel": "Digital",     "market": "SI",  "start": "2026-01-15", "end": "2026-02-28", "media_spend": 3200, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-002", "name": "Spring Events 2026",       "channel": "Events",      "market": "SI",  "start": "2026-03-01", "end": "2026-04-30", "media_spend": 4100, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
    ]
    mkt_df = pd.DataFrame(mkt_campaigns)
    mkt_df["total_spend"] = mkt_df["media_spend"] + mkt_df["listing_fee"] + mkt_df["trade_disc"]
    mkt_df["attributed_sales"] = 0.0

    return prim_df, so_df, mkt_df, stock_df, PRODUCTS

def load_excel(file):
    """
    Load Niamito_Master_Tables.xlsx and map all sheets to the app's
    internal dataframe schema.
    Returns (prim_df, so_df, mkt_df, stock_df, PRODUCTS, exp_df).
    """
    def to_float(val):
        """Safely convert a cell value to float, treating '-', '', None as 0."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    CHANNEL_TYPE_MAP = {
        # Old Slovenian type names
        "Ekipa": "Team",
        "Produkcija": "Production",
        "produkcija": "Production",
        "Digitalni marketing": "Digital",
        "Digitalni marketing AT": "Digital (AT)",
        "Dogodki & promocije": "Events",
        "Tradicionalni marketing": "Traditional",
        "Influencer": "Influencer",
        # New type names (current format)
        "Influencerji": "Influencer",
        "Media buy": "Digital",
        "Promocije - event": "Events",
        "Promocije - materiali": "Production",
        # English pass-throughs
        "Team": "Team",
        "Digital": "Digital",
        "Events": "Events",
        "Traditional": "Traditional",
        "Production": "Production",
    }

    import openpyxl as _opxl, re as _re

    def _cell_val(v):
        """Extract actual value from openpyxl cell — handles IFERROR formula wrappers that
        Google Sheets / Excel use to cache computed values (IMPORTRANGE, DUMMYFUNCTION, etc.).
        Works whether the workbook was opened with data_only=True (returns cached value directly)
        or data_only=False (returns the formula string, from which we extract the fallback value)."""
        if v is None:
            return None
        s = str(v)
        if not s.startswith("="):
            return v  # plain value — return as-is
        # General IFERROR fallback: match the last , "string" or , number before closing paren
        m = _re.search(r',\s*("([^"]*)"|([-]?\d+(?:\.\d+)?))\s*\)\s*$', s)
        if m:
            if m.group(2) is not None:    # quoted string fallback
                return m.group(2)
            try:
                return float(m.group(3))  # numeric fallback
            except Exception:
                pass
        return None  # formula with no usable fallback

    # Use data_only=True so openpyxl returns cached formula results (e.g. =F2*2.98 → 2145.6).
    # The workbook is always a user-supplied Excel file so cached values are present.
    _wb = _opxl.load_workbook(file, data_only=True)

    def _read_ws_rows(ws, header_row: int, data_start: int):
        """Read a worksheet into a list of dicts, extracting values from formula wrappers."""
        headers = [
            (str(_cell_val(cell.value)).replace("\n", " ").strip()
             if _cell_val(cell.value) is not None else f"_col{i}")
            for i, cell in enumerate(ws[header_row])
        ]
        rows = []
        for row in ws.iter_rows(min_row=data_start, values_only=False):
            extracted = [_cell_val(cell.value) for cell in row]
            if any(v is not None for v in extracted):
                rows.append(dict(zip(headers, extracted)))
        return headers, rows

    # Read sheets with row-3 headers (standard sheets)
    raw = {}
    _PLAIN_HDR = ("primary", "secondary")   # these sheets have header in row 1
    for s in _wb.sheetnames:
        try:
            ws = _wb[s]
            _use_plain = any(k in s.lower() for k in _PLAIN_HDR)
            _, rows = _read_ws_rows(ws,
                                    header_row=1 if _use_plain else 3,
                                    data_start=2 if _use_plain else 4)
            if rows:
                df = pd.DataFrame(rows).dropna(how="all")
                raw[s] = df
        except Exception:
            pass

    # Read Expenses sheet with row-1 headers
    exp_raw = None
    for s in _wb.sheetnames:
        if "expense" in s.lower() or "Expense" in s:
            try:
                ws = _wb[s]
                _, rows = _read_ws_rows(ws, header_row=1, data_start=2)
                if rows:
                    exp_raw = pd.DataFrame(rows).dropna(how="all")
            except Exception:
                pass
            break

    def find(keywords):
        for name, df in raw.items():
            if any(k.lower() in name.lower() for k in keywords):
                return df, name
        return None, None

    prod_raw_df, _ = find(["Product"])
    mkt_raw_df, _  = find(["Marketing", "Calendar"])
    prim_raw_df, _ = find(["Primary", "Sales"])

    # ── Sales Feed sheet → preferred primary sales source ────────────────────
    # Header at row 4, data from row 5. Columns: Month, SKU Code, Product Name,
    # Units Sold, Revenue ex-VAT (€), Product Line [auto], Year
    _sf_prim_rows = []
    _month_to_num = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
                     "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    for _sn in _wb.sheetnames:
        if "sales feed" in _sn.lower() or ("sales" in _sn.lower() and "feed" in _sn.lower()):
            _ws_sf = _wb[_sn]
            for _sfrow in _ws_sf.iter_rows(min_row=5, values_only=True):
                _mo_raw, _sku_raw, _nm_raw, _units_raw, _rev_raw, _prod_line, _yr_raw = \
                    (_sfrow[i] if i < len(_sfrow) else None for i in range(7))
                # Skip rows without SKU or units
                if not _sku_raw or (not _units_raw and not _rev_raw):
                    continue
                _mo_str = str(_mo_raw).strip() if _mo_raw else ""
                _mo_num = _month_to_num.get(_mo_str)
                if not _mo_num:
                    continue
                try:
                    _yr = int(float(_yr_raw))
                except (TypeError, ValueError):
                    continue
                _sf_prim_rows.append({
                    "Invoice Date": pd.Timestamp(_yr, _mo_num, 1),
                    "Internal SKU Code": str(_sku_raw).strip(),
                    "Product Name": str(_nm_raw).strip() if _nm_raw else str(_sku_raw).strip(),
                    "Bottles sold": _units_raw,
                    "Gross Revenue (€)": _rev_raw,
                    "Product Line": str(_prod_line).strip() if _prod_line else "",
                    "Market": "DE" if "- DE" in str(_sku_raw).upper() else "SI",
                })
            break
    if _sf_prim_rows:
        prim_raw_df = pd.DataFrame(_sf_prim_rows)

    # ── v9+ format: Primary Sales fallback (header in row 1) ─────────────────
    elif prim_raw_df is None:
        for _sn in _wb.sheetnames:
            if "primary" in _sn.lower() and "sales" in _sn.lower():
                _ws_ps = _wb[_sn]
                _r1c1  = _cell_val(_ws_ps.cell(1, 1).value)
                if _r1c1 and "Invoice Date" in str(_r1c1):
                    _, _ps_rows = _read_ws_rows(_ws_ps, header_row=1, data_start=2)
                    if _ps_rows:
                        prim_raw_df = pd.DataFrame(_ps_rows).dropna(how="all")
                break

    # Find Secondary Sales sheet — detect whether row 1 is notes or real header
    sec_raw_df = None
    sec_name = None
    for _sn in _wb.sheetnames:
        if "secondary" in _sn.lower():
            sec_name = _sn
            _ws_sec = _wb[_sn]
            _r1c1_sec = _cell_val(_ws_sec.cell(1, 1).value)
            if _r1c1_sec and "DATE" in str(_r1c1_sec).upper():
                # Row 1 is the real header
                _, _sec_rows = _read_ws_rows(_ws_sec, header_row=1, data_start=2)
            else:
                # Row 1 is a notes/instruction row; real header is row 2
                _, _sec_rows = _read_ws_rows(_ws_sec, header_row=2, data_start=3)
            if _sec_rows:
                sec_raw_df = pd.DataFrame(_sec_rows).dropna(how="all")
            break

    # Find Sell-out Template sheet
    sot_raw_df = None
    for name, df in raw.items():
        if "sell" in name.lower() and "template" in name.lower():
            sot_raw_df = df
            break
        if "sell" in name.lower() and name != sec_name:
            sot_raw_df = df
            break

    # ── PRODUCTS dict ─────────────────────────────────────────────────────────
    PRODUCTS = {}
    prod_by_ret_name = {}
    if prod_raw_df is not None:
        ret_name_col = next((c for c in prod_raw_df.columns if "Retailer SKU Name" in c), None)
        sku_col      = next((c for c in prod_raw_df.columns if "Internal SKU" in c), None)
        name_col     = next((c for c in prod_raw_df.columns if "Product Name" in c), None)
        for _, r in prod_raw_df.iterrows():
            if pd.isna(r.get(sku_col, None)):
                continue
            sku = str(r[sku_col]).strip()
            prd_name = str(r[name_col]).strip() if name_col else sku
            PRODUCTS[sku] = {"name": prd_name, "price": 0.0, "bpc": 1}
            if ret_name_col and pd.notna(r.get(ret_name_col)):
                key = str(r[ret_name_col]).strip().lower()
                prod_by_ret_name[key] = {"sku_id": sku, "sku_name": prd_name}

    if not PRODUCTS:
        PRODUCTS = {
            "APL05": {"name": "Fresh Meal Apple 390g",       "price": 4.20, "bpc": 1},
            "BLU05": {"name": "Fresh Meal Blueberry 390g",   "price": 4.20, "bpc": 1},
            "SPN05": {"name": "Fresh Meal Spinach 390g",     "price": 4.20, "bpc": 1},
            "STR05": {"name": "Fresh Meal Strawberry 390g",  "price": 4.20, "bpc": 1},
            "BLK05": {"name": "Blueberry Oat",               "price": 3.50, "bpc": 1},
            "CHK05": {"name": "Choco Oat",                   "price": 3.50, "bpc": 1},
            "PCK05": {"name": "Peach Oat",                   "price": 3.50, "bpc": 1},
            "COU05-DE": {"name": "Meal in a Bottle Cocoa 470ml",   "price": 3.80, "bpc": 1},
            "CKU05-DE": {"name": "Meal in a Bottle Cookie 470ml",  "price": 3.80, "bpc": 1},
            "VAU05-DE": {"name": "Meal in a Bottle Vanilla 470ml", "price": 3.80, "bpc": 1},
        }

    # ── Primary Sales → prim_df ───────────────────────────────────────────────
    prim_rows = []
    if prim_raw_df is not None:
        date_col_p = next((c for c in prim_raw_df.columns if "Invoice Date" in c or "Date" in c), None)
        # v9: "Market or Retailer"  |  old: "Market"
        mkt_col_p  = next((c for c in prim_raw_df.columns if "Market" in c), None)
        # v9: "SKU" (full name or code)  |  old: "Internal SKU Code"
        sku_col_p  = next((c for c in prim_raw_df.columns
                           if "Internal SKU Code" in c or "Internal SKU" in c
                           or c.strip() == "SKU"), None)
        name_col_p = next((c for c in prim_raw_df.columns if "Product Name" in c), None)
        # v9: "Quantity (PCS)"  |  old: "Bottles sold"
        btl_col_p  = next((c for c in prim_raw_df.columns
                           if "Bottles sold" in c or "Bottles Sold" in c or "Bottles" in c
                           or "Quantity" in c or "PCS" in c), None)
        gross_col  = next((c for c in prim_raw_df.columns if "Gross Revenue" in c), None)

        # v9 has "Market or Retailer" — retailer name, not market code
        _is_retailer_col = mkt_col_p and "Retailer" in mkt_col_p

        def _infer_market(raw_val: str, sku_str: str) -> str:
            v = raw_val.strip().upper()
            if v in ("SI", "SLO", "SLOVENIJA"):                         return "SI"
            if v in ("HR", "HRV", "HRVATSKA"):                          return "HR"
            if v in ("DE", "DEU", "DEUTSCHLAND"):                       return "DE"
            # Infer from SKU — DE products contain "- DE"
            if "- DE" in sku_str.upper() or sku_str.upper().endswith("DE"): return "DE"
            # Known SI retailers
            if any(k in v for k in ("PREMA","MERCATOR","SPAR","HOFER","PETROL",
                                    "PTIČKA","ŽITO","TUSCH","INTERSPAR SI")):  return "SI"
            # Known HR retailers
            if any(k in v for k in ("KONZUM","STUDENAC","TOMMY","PLODINE",
                                    "KAUFLAND HR","INTERSPAR HR")):             return "HR"
            return "SI"  # default

        def _resolve_sku(raw_sku: str):
            """Return (sku_id, sku_name) from raw value (full name or internal code)."""
            s = raw_sku.strip()
            if s in PRODUCTS:                          # exact internal code match
                return s, PRODUCTS[s]["name"]
            key = s.lower()
            if key in prod_by_ret_name:                # retailer name lookup
                info = prod_by_ret_name[key]
                return info["sku_id"], info["sku_name"]
            for code in PRODUCTS:                      # prefix match (e.g. "APL05 Organic…")
                if s.upper().startswith(code.upper()):
                    return code, PRODUCTS[code]["name"]
            return s, s                                # unknown — use raw as both id and name

        for _, r in prim_raw_df.iterrows():
            _sku_raw = r.get(sku_col_p)
            if _sku_raw is None or (isinstance(_sku_raw, float) and pd.isna(_sku_raw)):
                continue
            sku_str = str(_sku_raw).strip()
            if not sku_str:
                continue

            raw_date = r.get(date_col_p)
            try:
                week = pd.to_datetime(raw_date, errors="coerce")
            except Exception:
                week = pd.NaT

            _mkt_raw = str(r.get(mkt_col_p, "SI")).strip() if mkt_col_p else "SI"
            mkt = _infer_market(_mkt_raw, sku_str)

            sku_id, sku_name = _resolve_sku(sku_str)
            if name_col_p and pd.notna(r.get(name_col_p)):
                sku_name = str(r.get(name_col_p)).strip() or sku_name

            bottles = int(to_float(r.get(btl_col_p)))
            gross   = to_float(r.get(gross_col))

            # If Gross Revenue is blank, estimate from PRODUCTS list price
            if gross == 0 and bottles > 0:
                price = PRODUCTS.get(sku_id, {}).get("price", 0.0)
                gross = round(price * bottles, 2)

            if bottles == 0 and gross == 0:
                continue

            prim_rows.append({
                "week":           week,
                "market":         mkt,
                "sku_id":         sku_id,
                "sku_name":       sku_name,
                "cases":          0,
                "bottles":        bottles,
                "list_price":     round(gross / max(bottles, 1), 4),
                "gross_revenue":  gross,
                "trade_discount": 0.0,
                "net_revenue":    gross,
                "funnel_type":    "3-tier" if mkt in ("SI", "HR") else "2-tier",
            })

    prim_df = pd.DataFrame(prim_rows) if prim_rows else pd.DataFrame(
        columns=["week","market","sku_id","sku_name","cases","bottles",
                 "list_price","gross_revenue","trade_discount","net_revenue","funnel_type"])
    prim_df["category"] = prim_df["sku_name"].apply(get_product_category)

    stock_df = pd.DataFrame(
        columns=["week","market","cases_in","cases_out","stock_cases","stock_to_sales"])

    # ── Secondary Sales → so_df ───────────────────────────────────────────────
    so_rows = []

    def _parse_sec_date(raw_date):
        """Parse Secondary Sales date: handles DD.MM.YYYY / D.M.YY strings and datetime objects."""
        if raw_date is None:
            return pd.NaT
        import datetime as _dt2
        if isinstance(raw_date, (_dt2.datetime, _dt2.date)):
            return pd.Timestamp(raw_date)
        s = str(raw_date).strip()
        if _re.match(r"\d{1,2}\.\d{1,2}\.\d{2,4}", s):
            parts = s.split(".")
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                if y < 100:
                    y += 2000
                return pd.Timestamp(y, m, d)
            except Exception:
                pass
        return pd.to_datetime(s, errors="coerce")

    def _parse_secondary_row(r, date_col, retail_col, sku_col_s, pcs_col, rev_col=None, mkt_col=None):
        week     = _parse_sec_date(r.get(date_col))
        retailer = str(r.get(retail_col, "")).strip() if retail_col else ""
        sku_raw  = str(r.get(sku_col_s, "")).strip() if sku_col_s else ""
        prod_info = prod_by_ret_name.get(sku_raw.lower(), {"sku_id": sku_raw, "sku_name": sku_raw})
        units = int(to_float(r.get(pcs_col)))
        rev   = to_float(r.get(rev_col)) if rev_col else 0.0
        mkt_raw = str(r.get(mkt_col, "")).strip().upper() if mkt_col else "SI"
        market  = mkt_raw if mkt_raw in ("SI", "HR", "DE", "PL", "CH", "AT", "ME") else "SI"
        return {
            "week":            week,
            "market":          market,
            "retailer":        retailer,
            "sku_id":          prod_info["sku_id"],
            "sku_name":        prod_info["sku_name"],
            "bottles_sold":    units,
            "consumer_price":  round(rev / units, 2) if units > 0 and rev > 0 else 0.0,
            "sellout_revenue": round(rev, 2),
            "funnel_type":     "3-tier",
        }

    if sec_raw_df is not None:
        date_col_s   = next((c for c in sec_raw_df.columns if "DATE" in c.upper() or "Date" in c), None)
        retail_col_s = next((c for c in sec_raw_df.columns if "RETAIL" in c.upper() or "Store" in c or "Retail" in c), None)
        sku_col_s    = next((c for c in sec_raw_df.columns if c.upper() == "SKU" or "SKU" in c), None)
        pcs_col_s    = next((c for c in sec_raw_df.columns if c.upper() == "PCS" or "PCS" in c or "Units" in c), None)
        rev_col_s    = next((c for c in sec_raw_df.columns if "Revenue" in c or "REVENUE" in c.upper()), None)
        mkt_col_s    = next((c for c in sec_raw_df.columns if "Channel" in c or "CHANNEL" in c.upper() or "Market" in c), None)
        for _, r in sec_raw_df.iterrows():
            if pd.isna(r.get(pcs_col_s)):
                continue
            row_data = _parse_secondary_row(r, date_col_s, retail_col_s, sku_col_s, pcs_col_s, rev_col_s, mkt_col_s)
            if row_data["bottles_sold"] != 0 or row_data["sellout_revenue"] != 0:
                so_rows.append(row_data)

    # Sell-out Template — merge additional rows
    if sot_raw_df is not None:
        date_col_t  = next((c for c in sot_raw_df.columns if "Date" in c), None)
        store_col_t = next((c for c in sot_raw_df.columns if "Store" in c or "Retail" in c), None)
        mkt_col_t   = next((c for c in sot_raw_df.columns if "Market" in c), None)
        name_col_t  = next((c for c in sot_raw_df.columns if "Product Name" in c), None)
        units_col_t = next((c for c in sot_raw_df.columns if "Units" in c), None)
        rev_col_t   = next((c for c in sot_raw_df.columns if "Revenue" in c), None)
        for _, r in sot_raw_df.iterrows():
            if pd.isna(r.get(units_col_t)):
                continue
            raw_date = r.get(date_col_t)
            try:
                week = pd.to_datetime(raw_date, errors="coerce")
            except Exception:
                week = pd.NaT
            mkt = str(r.get(mkt_col_t, "SI")).strip() if mkt_col_t else "SI"
            if mkt.upper() in ("SLO", "SLOVENIJA"):
                mkt = "SI"
            if mkt not in ("SI", "HR", "DE"):
                mkt = "SI"
            prd_raw = str(r.get(name_col_t, "")).strip() if name_col_t else ""
            prod_info = prod_by_ret_name.get(prd_raw.lower(), {"sku_id": prd_raw, "sku_name": prd_raw})
            units = int(to_float(r.get(units_col_t)))
            rev   = to_float(r.get(rev_col_t)) if rev_col_t else 0.0
            if units > 0:
                so_rows.append({
                    "week":            week,
                    "market":          mkt,
                    "retailer":        str(r.get(store_col_t, "")).strip() if store_col_t else "",
                    "sku_id":          prod_info["sku_id"],
                    "sku_name":        prod_info["sku_name"],
                    "bottles_sold":    units,
                    "consumer_price":  round(rev / units, 2) if units > 0 and rev > 0 else 0.0,
                    "sellout_revenue": round(rev, 2),
                    "funnel_type":     "3-tier" if mkt in ("SI", "HR") else "2-tier",
                })

    so_df = pd.DataFrame(so_rows) if so_rows else pd.DataFrame(
        columns=["week","market","retailer","sku_id","sku_name","bottles_sold",
                 "consumer_price","sellout_revenue","funnel_type"])
    if not so_df.empty:
        so_df["category"] = so_df["sku_name"].apply(get_product_category)
    else:
        so_df["category"] = pd.Series(dtype=str)

    # ── Marketing Calendar → mkt_df ───────────────────────────────────────────
    mkt_rows = []
    # Read directly from openpyxl to avoid duplicate-header overwrite bug
    _ws_mkt = None
    for _sn in _wb.sheetnames:
        if "marketing" in _sn.lower() or "calendar" in _sn.lower():
            _ws_mkt = _wb[_sn]
            break

    if _ws_mkt is not None:
        _mkt_all_rows = list(_ws_mkt.iter_rows(values_only=True))
        _mkt_hdrs = [str(c).strip() if c else f"_col{i}" for i, c in enumerate(_mkt_all_rows[2])]

        # Map header names to indices (first occurrence wins)
        _hmap = {}
        for _i, _h in enumerate(_mkt_hdrs):
            if _h not in _hmap:
                _hmap[_h] = _i

        def _mkt_get(row, key, default=None):
            idx = _hmap.get(key)
            if idx is None:
                return default
            return row[idx] if idx < len(row) else default

        def _parse_mkt_date(raw):
            """Handle both Excel datetime objects and DD.MM.YYYY strings."""
            if raw is None:
                return ""
            import datetime as _dt
            if isinstance(raw, (_dt.datetime, _dt.date)):
                return raw.strftime("%Y-%m-%d")
            s = str(raw).strip()
            # DD.MM.YYYY or DD.MM.YY
            if _re.match(r"\d{1,2}\.\d{1,2}\.\d{2,4}", s):
                parts = s.split(".")
                try:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    if y < 100:
                        y += 2000
                    return f"{y:04d}-{m:02d}-{d:02d}"
                except Exception:
                    pass
            return s[:10]

        for _source_row, _row in enumerate(_mkt_all_rows[3:], start=4):
            if not any(v is not None for v in _row):
                continue
            cid      = _mkt_get(_row, "Campaign ID")
            cam_name = str(_mkt_get(_row, "Campaign Name") or "").strip()
            # Skip rows with neither an ID nor a campaign name
            if not cam_name and cid is None:
                continue
            # Spend at column INDEX 6 always (first "TOTAL Spend (€)")
            total_spend_raw = _row[6] if len(_row) > 6 else None
            total = to_float(total_spend_raw)
            if total == 0:
                continue  # skip placeholder rows with no spend

            raw_type = str(_mkt_get(_row, "Type") or "Unassigned").strip()
            channel  = CHANNEL_TYPE_MAP.get(raw_type, raw_type)

            mkt_val = str(_mkt_get(_row, "Market") or "").strip()
            if mkt_val.upper() in ("SLO", "SLOVENIJA"):
                mkt_val = "SI"
            if not mkt_val:
                mkt_val = "Unassigned"

            start_raw = _mkt_get(_row, "Start Date")
            end_raw   = _mkt_get(_row, "End Date")
            start_str = _parse_mkt_date(start_raw)
            end_str   = _parse_mkt_date(end_raw)

            inf_val   = _mkt_get(_row, "Influencer Handle")
            reach_val = _mkt_get(_row, "Estimated Reach")
            scope_raw = _mkt_get(_row, "Attribution Scope")
            window_raw= _mkt_get(_row, "Attribution Window (days)")

            if scope_raw and pd.notna(scope_raw):
                scope = "Market" if "market" in str(scope_raw).lower() else "Store"
            else:
                scope = "Market" if channel in ("Digital","Digital-Intl","Events","Traditional") else "Store"

            inf_clean  = str(inf_val).strip() if inf_val and str(inf_val).strip() not in ("None","nan","") else None
            reach_clean = to_float(reach_val) or None

            mkt_rows.append({
                "id":               str(cid).strip() if cid is not None else "",
                "source_row":       _source_row,
                "product_family":   _mkt_get(_row, "Product Family") or _mkt_get(_row, "Product Line") or "",
                "segment":          _mkt_get(_row, "Segment") or "",
                "retailer":         _mkt_get(_row, "Retailer") or _mkt_get(_row, "Store") or "",
                "name":             cam_name,
                "channel":          channel,
                "source_type":      raw_type,
                "market":           mkt_val,
                "start":            start_str,
                "end":              end_str,
                "media_spend":      total,
                "listing_fee":      to_float(_mkt_get(_row, "Listing Fees (€)")),
                "trade_disc":       to_float(_mkt_get(_row, "Trade Discounts (€)")),
                "total_spend":      total,
                "roas":             None,
                "attributed_sales": (to_float(_mkt_get(_row, "Attributed Revenue (€)"))
                                     if _mkt_get(_row, "Attributed Revenue (€)") is not None else None),
                "influencer":       inf_clean,
                "reach":            reach_clean,
                "scope":            scope,
                "window_days":      int(to_float(window_raw) or 14),
            })

    mkt_df = pd.DataFrame(mkt_rows) if mkt_rows else pd.DataFrame(
        columns=["id","name","channel","market","start","end","media_spend",
                 "listing_fee","trade_disc","total_spend","roas","attributed_sales",
                 "influencer","reach","scope","window_days"])

    # ── Expenses → exp_df + stock/promo from Excel ───────────────────────────
    exp_rows = []
    # ── Read Cost Allocation section directly from worksheet (own column layout) ─
    # Structure: section header → instruction → col headers (Month|Stock|Promo|Internal) → 12 month rows
    _ALLOC_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    # Per-month dicts; summed for waterfall totals, kept for future monthly charts
    _alloc = {m: {"stock": 0.0, "promo": 0.0, "internal": 0.0} for m in _ALLOC_MONTHS}
    _xl_stock_val = _xl_promo_val = _xl_internal_val = 0.0

    _ws_exp = None
    for _sn in _wb.sheetnames:
        if "expense" in _sn.lower():
            _ws_exp = _wb[_sn]; break

    if _ws_exp is not None:
        # Find section header row by scanning col A for "COST ALLOCATION"
        _sec_row = None
        for _r in _ws_exp.iter_rows(min_col=1, max_col=1, values_only=False):
            _v = _cell_val(_r[0].value)
            if _v and "COST ALLOCATION" in str(_v).upper():
                _sec_row = _r[0].row; break
        if _sec_row is not None:
            _data_start = _sec_row + 3
            # Detect format by checking if first data cell is a month name (new monthly table)
            # or a type label like "Active Stock" (old single-row format)
            _first_cell = _cell_val(_ws_exp.cell(_data_start, 1).value)
            _is_monthly = str(_first_cell).strip() in _ALLOC_MONTHS if _first_cell else False

            if _is_monthly:
                # ── New format: rows are months, cols 2/3/4 = stock/promo/internal ──
                for _ri in range(_data_start, _data_start + 12):
                    _mo = _cell_val(_ws_exp.cell(_ri, 1).value)
                    if _mo not in _ALLOC_MONTHS:
                        break
                    _alloc[_mo]["stock"]    = to_float(_cell_val(_ws_exp.cell(_ri, 2).value))
                    _alloc[_mo]["promo"]    = to_float(_cell_val(_ws_exp.cell(_ri, 3).value))
                    _alloc[_mo]["internal"] = to_float(_cell_val(_ws_exp.cell(_ri, 4).value))
            else:
                # ── Old format: rows are types (Active Stock / Promo / Internal),
                #    col 3 = Amount (€) possibly stored as "0,00 €" string ──
                def _parse_euro_str(v):
                    """Parse '1.234,56 €' or '1234.56' or float → float."""
                    if v is None: return 0.0
                    s = str(v).replace("€","").replace(" ","").replace(".","").replace(",",".")
                    try: return float(s)
                    except: return 0.0
                for _ri in range(_data_start, _data_start + 10):
                    _type = _cell_val(_ws_exp.cell(_ri, 1).value)
                    if not _type: continue
                    _type_s = str(_type).strip()
                    _amt = _parse_euro_str(_cell_val(_ws_exp.cell(_ri, 3).value))
                    if _type_s == "Active Stock":
                        _xl_stock_val = _amt
                    elif _type_s == "Promo & External":
                        _xl_promo_val = _amt
                    elif _type_s == "Internal Consumption":
                        _xl_internal_val = _amt

            _xl_stock_val    = _xl_stock_val    or sum(v["stock"]    for v in _alloc.values())
            _xl_promo_val    = _xl_promo_val    or sum(v["promo"]    for v in _alloc.values())
            _xl_internal_val = _xl_internal_val or sum(v["internal"] for v in _alloc.values())

    # ── Parse expense data rows (skip allocation section) ────────────────────
    if exp_raw is not None:
        pl_col        = next((c for c in exp_raw.columns if "Product Line" in c), None)
        sku_col_e     = next((c for c in exp_raw.columns if c.strip() == "SKU"), None)
        mon_col       = next((c for c in exp_raw.columns if "Month" in c), None)
        mat_col       = next((c for c in exp_raw.columns if "Material Cost" in c), None)
        lab_col       = next((c for c in exp_raw.columns if "Labour Cost" in c or "Labor Cost" in c), None)
        ovh_col       = next((c for c in exp_raw.columns if "Production Overhead" in c), None)
        prod_col      = next((c for c in exp_raw.columns if "Production cost" in c
                              and "Material" not in c and "Labour" not in c
                              and "Labor" not in c and "Overhead" not in c), None)
        log_col       = next((c for c in exp_raw.columns if "Logistics" in c), None)
        mktg_col      = next((c for c in exp_raw.columns if "Marketing" in c and "Promo" in c), None)
        if mktg_col is None:
            mktg_col  = next((c for c in exp_raw.columns if "Marketing" in c), None)
        promo_u_col   = next((c for c in exp_raw.columns if "Promotional Units" in c), None)
        act_stock_col = next((c for c in exp_raw.columns if "Active Stock" in c), None)
        int_usage_col = next((c for c in exp_raw.columns if "Internal Usage" in c), None)
        _SKIP_PREFIXES = ("COST ALLOCATION", "Enter ", "Month", "Active", "Promo &", "Internal")
        for _, r in exp_raw.iterrows():
            pl_val = r.get(pl_col)
            if pl_val is None or (isinstance(pl_val, float) and pd.isna(pl_val)):
                continue
            pl_str = str(pl_val).strip()
            # Skip allocation section rows (header, note, column labels, month rows)
            if pl_str.startswith(_SKIP_PREFIXES) or pl_str in _ALLOC_MONTHS:
                continue
            # Derive material / labour+overhead from dedicated columns when present;
            # fall back to splitting production_cost 50/50 if columns are absent.
            mat_val  = to_float(r.get(mat_col))  if mat_col  else None
            lab_val  = to_float(r.get(lab_col))  if lab_col  else None
            ovh_val  = to_float(r.get(ovh_col))  if ovh_col  else 0.0
            prod_tot = to_float(r.get(prod_col))  if prod_col else (
                           (mat_val or 0) + (lab_val or 0) + ovh_val)
            if mat_val is None:
                mat_val = prod_tot * 0.5
            labour_overhead = prod_tot - mat_val  # labour + overhead combined
            exp_rows.append({
                "product_line":    pl_str,
                "sku":             str(r.get(sku_col_e, "")).strip() if sku_col_e else "",
                "month":           str(r.get(mon_col, "")).strip() if mon_col else "",
                "material_cost":   mat_val,
                "labour_overhead": labour_overhead,
                "production_cost": prod_tot,
                "logistics":       to_float(r.get(log_col)),
                "marketing_promo": to_float(r.get(mktg_col)),
                "promo_units":     to_float(r.get(promo_u_col))   if promo_u_col   else 0.0,
                "active_stock":    abs(to_float(r.get(act_stock_col))) if act_stock_col else 0.0,
                "internal_usage":  abs(to_float(r.get(int_usage_col))) if int_usage_col else 0.0,
            })

    exp_df = pd.DataFrame(exp_rows) if exp_rows else pd.DataFrame(
        columns=["product_line","sku","month","material_cost","labour_overhead",
                 "production_cost","logistics","marketing_promo",
                 "promo_units","active_stock","internal_usage"])

    return prim_df, so_df, mkt_df, stock_df, PRODUCTS, exp_df, _xl_stock_val, _xl_promo_val, _xl_internal_val
