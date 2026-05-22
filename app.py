# ============================================================
# UNIFIED OPTIONS TRADING DASHBOARD
# ============================================================
# One app — full workflow:
#   1. Macro regime (always visible — read this first)
#   2. Trade Ideas — income and growth candidates with
#      specific strategy suggestions and IBKR sizing
#   3. ETF Sector Screener — what sectors are moving
#   4. Holdings Drill-Down — leading stocks inside sectors
#   5. Options Filter — IV, earnings, signal per stock
#
# Run:  streamlit run dashboard.py
# ============================================================

import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Options Trading Dashboard",
    page_icon="🎯",
    layout="wide",
)

# ============================================================
# CONFIG — EDIT THESE LISTS TO CUSTOMISE YOUR UNIVERSE
# ============================================================

# -- ETF sectors (for sector screener tab) -------------------
ETF_SECTORS = {
    "Broad Market":         [("SPY","SPDR S&P 500"),("QQQ","Invesco QQQ"),("IVV","iShares S&P 500"),("VTI","Vanguard Total Market"),("IWM","iShares Russell 2000")],
    "Nasdaq / Growth":      [("QQQ","Invesco QQQ"),("AMOM","QRAFT AI Momentum")],
    "Technology":           [("XLK","Tech Select Sector"),("SKYY","First Trust Cloud"),("CIBR","First Trust Cybersecurity"),("IGV","iShares Software"),("SOCL","Global X Social Media")],
    "Semiconductors":       [("SMH","VanEck Semiconductors"),("SOXX","iShares Semiconductors")],
    "Robotics / AI":        [("BOTZ","Global X Robotics & AI")],
    "Data Centers":         [("SRVR","Pacer Data & Infrastructure")],
    "Fintech / Blockchain": [("FINX","Global X FinTech"),("BLOK","Amplify Blockchain"),("MILN","Global X Millennials")],
    "Clean Energy / EV":    [("TAN","Invesco Solar"),("DRIV","Global X EV"),("ICLN","iShares Clean Energy"),("LIT","Global X Lithium"),("URA","Global X Uranium")],
    "Energy":               [("XLE","Energy Select Sector"),("XOP","SPDR Oil & Gas Exploration"),("OIH","VanEck Oil Services")],
    "Space":                [("UFO","Procure Space ETF")],
    "Industrials":          [("XLI","Industrials Select"),("IYT","iShares Transportation"),("ITA","iShares Aerospace & Defense"),("PAVE","Global X Infrastructure")],
    "Materials":            [("XLB","Materials Select"),("GDX","VanEck Gold Miners"),("SIL","Global X Silver Miners"),("REMX","VanEck Rare Earth")],
    "Consumer Discr":       [("XLY","Consumer Discr Select"),("XRT","SPDR Retail"),("PEJ","Invesco Leisure"),("ITB","iShares Homebuilders")],
    "Consumer Staples":     [("XLP","Consumer Staples Select"),("DBA","Invesco Agriculture"),("PBJ","Invesco Food & Bev"),("PPH","VanEck Pharma")],
    "Healthcare":           [("XLV","Healthcare Select"),("IBB","iShares Biotech"),("XBI","SPDR Biotech"),("IHI","iShares Med Devices"),("ARKG","ARK Genomics")],
    "Financials":           [("XLF","Financials Select"),("KBE","SPDR Bank"),("KRE","SPDR Regional Banking"),("KIE","SPDR Insurance")],
    "Utilities":            [("XLU","Utilities Select"),("VPU","Vanguard Utilities"),("PHO","Invesco Water")],
    "Real Estate":          [("VNQ","Vanguard Real Estate"),("IFGL","iShares Intl Real Estate")],
    "Communication":        [("VOX","Vanguard Communication"),("XLC","Communication Select"),("METV","Roundhill Metaverse")],
    "Macro / Rates":        [("TLT","iShares 20Y Treasury"),("HYG","iShares High Yield"),("GLD","SPDR Gold"),("SLV","iShares Silver")],
    "International":        [("KWEB","KraneShares China Internet"),("FXI","iShares China Large Cap"),("EEM","iShares Emerging Markets")],
    "High Vol / Spec":      [("ARKK","ARK Innovation"),("JETS","US Global Airlines"),("XHB","SPDR Homebuilders")],
}

# -- Stock universe for trade ideas --------------------------
# US stocks: most liquid options, tight spreads on IBKR
# UK stocks: listed as US ADRs — trade these on IBKR for
#            better options liquidity than UK-listed options
STOCK_UNIVERSE = {
    # ── US Technology ─────────────────────────────────────
    "NVDA":  ("NVIDIA",             "Technology", "US"),
    "AAPL":  ("Apple",              "Technology", "US"),
    "MSFT":  ("Microsoft",          "Technology", "US"),
    "META":  ("Meta",               "Technology", "US"),
    "GOOGL": ("Alphabet",           "Technology", "US"),
    "AMZN":  ("Amazon",             "Technology", "US"),
    "AMD":   ("AMD",                "Technology", "US"),
    "AVGO":  ("Broadcom",           "Technology", "US"),
    "CRM":   ("Salesforce",         "Technology", "US"),
    "NOW":   ("ServiceNow",         "Technology", "US"),
    "CRWD":  ("CrowdStrike",        "Technology", "US"),
    "PANW":  ("Palo Alto Networks", "Technology", "US"),
    "SNOW":  ("Snowflake",          "Technology", "US"),
    # ── US Semiconductors ─────────────────────────────────
    "MU":    ("Micron",             "Semiconductors", "US"),
    "QCOM":  ("Qualcomm",           "Semiconductors", "US"),
    "TSM":   ("Taiwan Semi",        "Semiconductors", "US"),
    "AMAT":  ("Applied Materials",  "Semiconductors", "US"),
    "INTC":  ("Intel",              "Semiconductors", "US"),
    # ── US Financials ─────────────────────────────────────
    "JPM":   ("JPMorgan",           "Financials", "US"),
    "GS":    ("Goldman Sachs",      "Financials", "US"),
    "BAC":   ("Bank of America",    "Financials", "US"),
    "MS":    ("Morgan Stanley",     "Financials", "US"),
    "V":     ("Visa",               "Financials", "US"),
    "MA":    ("Mastercard",         "Financials", "US"),
    # ── US Healthcare ─────────────────────────────────────
    "LLY":   ("Eli Lilly",          "Healthcare", "US"),
    "UNH":   ("UnitedHealth",       "Healthcare", "US"),
    "ABBV":  ("AbbVie",             "Healthcare", "US"),
    "MRK":   ("Merck",              "Healthcare", "US"),
    "AMGN":  ("Amgen",              "Healthcare", "US"),
    "VRTX":  ("Vertex Pharma",      "Healthcare", "US"),
    # ── US Energy ─────────────────────────────────────────
    "XOM":   ("ExxonMobil",         "Energy", "US"),
    "CVX":   ("Chevron",            "Energy", "US"),
    "COP":   ("ConocoPhillips",     "Energy", "US"),
    "SLB":   ("SLB",                "Energy", "US"),
    # ── US Consumer / Other ───────────────────────────────
    "TSLA":  ("Tesla",              "Consumer Discr", "US"),
    "HD":    ("Home Depot",         "Consumer Discr", "US"),
    "COST":  ("Costco",             "Consumer Staples", "US"),
    "NFLX":  ("Netflix",            "Communication", "US"),
    "DIS":   ("Disney",             "Communication", "US"),
    # ── ETFs (liquid options, good for income plays) ──────
    "SPY":   ("SPDR S&P 500",       "Broad Market", "ETF"),
    "QQQ":   ("Invesco QQQ",        "Broad Market", "ETF"),
    "IWM":   ("Russell 2000",       "Broad Market", "ETF"),
    "GLD":   ("SPDR Gold",          "Commodities",  "ETF"),
    "TLT":   ("iShares 20Y Bonds",  "Rates",        "ETF"),
    # ── UK stocks (US-listed ADRs — better options liquidity
    #    than trading UK-listed options on IBKR) ───────────
    "AZN":   ("AstraZeneca",        "Healthcare",   "UK-ADR"),
    "GSK":   ("GSK plc",            "Healthcare",   "UK-ADR"),
    "BP":    ("BP plc",             "Energy",       "UK-ADR"),
    "SHEL":  ("Shell plc",          "Energy",       "UK-ADR"),
    "HSBC":  ("HSBC Holdings",      "Financials",   "UK-ADR"),
    "RIO":   ("Rio Tinto",          "Materials",    "UK-ADR"),
    "VOD":   ("Vodafone",           "Communication","UK-ADR"),
    "BCS":   ("Barclays",           "Financials",   "UK-ADR"),
    "LYG":   ("Lloyds Banking",     "Financials",   "UK-ADR"),
    "LSXMA": ("Liberty Media",      "Communication","UK-ADR"),
}

# Macro tickers
MACRO_TICKERS = {
    "VIX":             "^VIX",
    "Gold":            "GC=F",
    "Crude Oil":       "CL=F",
    "US Dollar (DXY)": "DX-Y.NYB",
    "10Y Treasury":    "^TNX",
    "2Y Treasury":     "^IRX",
    "HYG":             "HYG",
    "TLT":             "TLT",
    "SPY":             "^GSPC",
    "RSP":             "RSP",
    "IWM":             "IWM",
}

# GBP/USD rate for sizing (approximation)
GBPUSD = 1.27


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def gbp(usd_amount):
    """Convert USD to GBP string."""
    return f"£{usd_amount / GBPUSD:,.0f}"


def safe_float(val, default=None):
    try:
        return float(val)
    except Exception:
        return default


def pct(val):
    if val is None:
        return "N/A"
    return f"{val:+.1f}%"


def color_val(val, good_positive=True):
    """Return green/red based on value sign."""
    if val is None:
        return "gray"
    if good_positive:
        return "#16a34a" if val >= 0 else "#dc2626"
    return "#dc2626" if val >= 0 else "#16a34a"


# ============================================================
# DATA FETCHING
# ============================================================

@st.cache_data(ttl=300)
def fetch_macro_snapshot():
    """
    Fetch all macro indicators in one pass.
    Returns dict of current values and % changes.
    """
    result = {}
    for name, ticker in MACRO_TICKERS.items():
        try:
            t    = yf.Ticker(ticker)
            info = t.info
            price = (info.get("regularMarketPrice")
                     or info.get("currentPrice")
                     or info.get("previousClose"))
            hist  = t.history(period="1mo")
            if not hist.empty and price:
                prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else float(hist["Close"].iloc[-1])
                chg_1d = round((float(price) - prev_close) / prev_close * 100, 2)
                start  = float(hist["Close"].iloc[0])
                chg_1m = round((float(price) - start) / start * 100, 2)
                result[name] = {
                    "price": round(float(price), 2),
                    "chg_1d": chg_1d,
                    "chg_1m": chg_1m,
                }
        except Exception:
            pass
    return result


@st.cache_data(ttl=300)
def detect_regime_quick(macro):
    """
    Fast regime classification from macro snapshot.
    Returns (regime_label, colour, short_description, bias)
    """
    risk_off = 0
    risk_on  = 0

    vix = macro.get("VIX", {}).get("price")
    vix_chg = macro.get("VIX", {}).get("chg_1d")
    gold_chg = macro.get("Gold", {}).get("chg_1d")
    hyg_chg  = macro.get("HYG", {}).get("chg_1d")
    spy_chg  = macro.get("SPY", {}).get("chg_1d")
    oil_chg  = macro.get("Crude Oil", {}).get("chg_1d")
    dxy_chg  = macro.get("US Dollar (DXY)", {}).get("chg_1d")

    if vix:
        if vix >= 35:   risk_off += 3
        elif vix >= 25: risk_off += 2
        elif vix <= 15: risk_on  += 2
        else:           risk_on  += 1

    if vix_chg:
        if vix_chg >= 10:  risk_off += 2
        elif vix_chg >= 5: risk_off += 1
        elif vix_chg <= -10: risk_on += 2
        elif vix_chg <= -5:  risk_on += 1

    if gold_chg:
        if gold_chg >= 2:  risk_off += 2
        elif gold_chg <= -1: risk_on += 1

    if hyg_chg:
        if hyg_chg <= -1:  risk_off += 3
        elif hyg_chg >= 1: risk_on  += 2

    if spy_chg:
        if spy_chg >= 2:   risk_on  += 2
        elif spy_chg >= 1: risk_on  += 1
        elif spy_chg <= -2: risk_off += 2
        elif spy_chg <= -1: risk_off += 1

    # Stagflation check
    stag = (oil_chg or 0) >= 3 and (dxy_chg or 0) >= 1

    if stag and risk_off >= 2:
        return ("⚠️ Stagflation Risk", "#b45309",
                "Oil + dollar surging. Growth stocks squeezed. Favour energy/commodities.",
                "puts")

    if risk_off >= 5:
        return ("🔴 Risk-Off", "#dc2626",
                f"VIX {vix:.0f} — fear dominant. HYG falling. Focus on puts and selling premium.",
                "puts")

    if risk_off >= 3:
        return ("🟠 Cautious", "#ea580c",
                "Mixed but leaning risk-off. Reduce size. Use spreads, not naked options.",
                "reduce")

    if risk_on >= 4:
        return ("🟢 Risk-On", "#16a34a",
                f"VIX {vix:.0f} — low fear, credit healthy. Favour calls on leading sectors.",
                "calls")

    if risk_on >= 2:
        return ("🟡 Mildly Risk-On", "#ca8a04",
                "Positive but not euphoric. Selective calls. Monitor for changes.",
                "calls")

    return ("🟡 Neutral", "#6b7280",
            "No dominant signal. Use defined-risk spreads. Wait for clarity.",
            "neutral")


@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    """
    Fetch everything needed to evaluate a trade idea for one stock:
    price, IV, HV30, earnings, momentum, 52W range.
    """
    try:
        t    = yf.Ticker(ticker)
        info = t.info
        price = safe_float(
            info.get("regularMarketPrice") or info.get("currentPrice")
        )
        if not price:
            return None

        low52  = safe_float(info.get("fiftyTwoWeekLow",  0))
        high52 = safe_float(info.get("fiftyTwoWeekHigh", 0))
        range_pct = (
            round((price - low52) / (high52 - low52) * 100, 1)
            if high52 and high52 != low52 else None
        )

        # Historical volatility (30-day annualised)
        hist = t.history(period="3mo", auto_adjust=True)
        hv30 = None
        if len(hist) >= 30:
            lr   = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
            hv30 = round(float(lr.tail(30).std() * np.sqrt(252) * 100), 1)

        # 1-month momentum
        mom_1m = None
        if len(hist) >= 21:
            mom_1m = round(
                (float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[-21]))
                / float(hist["Close"].iloc[-21]) * 100, 1
            )

        # IV from nearest ATM option
        iv = None
        options_vol = None
        pc_ratio    = None
        try:
            dates = t.options
            if dates:
                chain = t.option_chain(dates[0])
                calls = chain.calls
                puts  = chain.puts
                atm   = calls.iloc[(calls["strike"] - price).abs().argsort()[:1]]
                if not atm.empty:
                    iv = round(float(atm["impliedVolatility"].values[0]) * 100, 1)
                cv = calls["volume"].fillna(0).sum()
                pv = puts["volume"].fillna(0).sum()
                options_vol = int(cv + pv)
                if cv > 0:
                    pc_ratio = round(pv / cv, 2)
        except Exception:
            pass

        # IV rank proxy (IV vs HV — higher = more expensive)
        iv_rank_proxy = None
        if iv and hv30:
            iv_rank_proxy = round(iv / hv30 * 50, 0)  # scale to ~0-100
            iv_rank_proxy = min(100, max(0, iv_rank_proxy))

        # Earnings date (3 methods)
        earnings = None
        try:
            ts = info.get("earningsTimestampNext") or info.get("earningsTimestamp")
            if ts:
                dt = pd.Timestamp(ts, unit="s")
                if dt > pd.Timestamp.now():
                    earnings = dt.date()
        except Exception:
            pass

        if not earnings:
            try:
                cal = t.calendar
                if cal and "Earnings Date" in cal:
                    for d in cal["Earnings Date"]:
                        ts = pd.Timestamp(d)
                        if ts.tzinfo:
                            ts = ts.tz_localize(None)
                        if ts > pd.Timestamp.now():
                            earnings = ts.date()
                            break
            except Exception:
                pass

        earnings_days = None
        if earnings:
            earnings_days = (pd.Timestamp(str(earnings)) - pd.Timestamp.now()).days

        # Average daily volume
        avg_vol = safe_float(info.get("averageVolume"))

        return {
            "ticker":        ticker,
            "name":          STOCK_UNIVERSE.get(ticker, (ticker, "", ""))[0],
            "sector":        STOCK_UNIVERSE.get(ticker, ("", "", ""))[1],
            "market":        STOCK_UNIVERSE.get(ticker, ("", "", ""))[2],
            "price":         price,
            "range_pct":     range_pct,
            "hv30":          hv30,
            "iv":            iv,
            "iv_rank_proxy": iv_rank_proxy,
            "mom_1m":        mom_1m,
            "pc_ratio":      pc_ratio,
            "options_vol":   options_vol,
            "earnings":      str(earnings) if earnings else None,
            "earnings_days": earnings_days,
            "avg_vol":       avg_vol,
        }
    except Exception:
        return None


def generate_income_idea(d, regime_bias):
    """
    Given stock data dict, generate an income (sell premium) trade idea.
    Returns dict with trade details or None if stock not suitable.

    Income plays work best when:
    - IV is high (you collect more premium)
    - Stock is range-bound or mildly trending
    - No earnings within 30 days (earnings cause IV spikes
      which would hurt short premium positions)
    - Options are liquid (tight spreads on IBKR)
    """
    if not d or not d["iv"] or not d["hv30"] or not d["price"]:
        return None

    iv_rank = d["iv_rank_proxy"] or 0
    iv      = d["iv"]
    price   = d["price"]
    hv30    = d["hv30"]

    # Income criteria:
    # IV rank > 50 means options are expensive relative to
    # actual moves — good time to sell premium
    if iv_rank < 45:
        return None

    # Avoid earnings within 30 days:
    # When earnings approach, IV spikes dramatically.
    # If you're short premium, this spike works against you.
    if d["earnings_days"] and d["earnings_days"] < 30:
        return None

    # Need liquid options
    if d["options_vol"] and d["options_vol"] < 500:
        return None

    # Calculate suggested put spread strikes
    # Sell put at ~5-7% below current price (below support)
    # Buy put 5 points lower (defines your max risk)
    sell_put  = round(price * 0.93, 0)  # 7% OTM
    buy_put   = sell_put - 5            # $5 wide spread

    # Estimated premium (rough: ~30% of spread width when IV is elevated)
    est_premium_per_share = round((sell_put - buy_put) * 0.30 * (iv_rank / 100), 2)
    est_premium_per_share = max(est_premium_per_share, 0.30)
    est_premium_contract  = round(est_premium_per_share * 100, 0)
    max_risk_contract     = (sell_put - buy_put - est_premium_per_share) * 100
    max_risk_contract     = max(max_risk_contract, 100)

    # How many contracts for £700 max risk
    max_risk_gbp = 700
    max_risk_usd = max_risk_gbp * GBPUSD
    contracts    = max(1, int(max_risk_usd / max_risk_contract))

    # Score the idea — higher is better income candidate
    score = 0
    score += min(40, iv_rank * 0.4)             # IV rank (max 40pts)
    if d["earnings_days"] and d["earnings_days"] > 45:
        score += 20                              # plenty of time before earnings
    elif d["earnings_days"] and d["earnings_days"] > 30:
        score += 10
    if d["options_vol"] and d["options_vol"] > 5000:
        score += 20                              # very liquid
    elif d["options_vol"] and d["options_vol"] > 1000:
        score += 10
    if d["range_pct"] and 30 < d["range_pct"] < 70:
        score += 20                              # mid-range = range-bound

    return {
        "type":                "income",
        "ticker":              d["ticker"],
        "name":                d["name"],
        "sector":              d["sector"],
        "market":              d["market"],
        "price":               price,
        "iv":                  iv,
        "iv_rank_proxy":       iv_rank,
        "hv30":                hv30,
        "range_pct":           d["range_pct"],
        "mom_1m":              d["mom_1m"],
        "earnings":            d["earnings"],
        "earnings_days":       d["earnings_days"],
        "options_vol":         d["options_vol"],
        "sell_put":            sell_put,
        "buy_put":             buy_put,
        "est_premium":         est_premium_contract,
        "max_risk_contract":   max_risk_contract,
        "contracts":           contracts,
        "score":               round(score, 0),
        "strategy":            f"Sell ${sell_put:.0f}/${buy_put:.0f} Put Spread",
    }


def generate_growth_idea(d, regime_bias, sector_strong=True):
    """
    Given stock data dict, generate a growth (buy options) trade idea.
    Returns dict with trade details or None if stock not suitable.

    Growth plays work best when:
    - Stock has clear directional momentum
    - IV is low (options are cheap — you're buying)
    - Sector is in a strong trend (tailwind behind the trade)
    - No earnings within 14 days (unless intentionally trading earnings)
    """
    if not d or not d["iv"] or not d["hv30"] or not d["price"]:
        return None

    iv_rank = d["iv_rank_proxy"] or 0
    iv      = d["iv"]
    price   = d["price"]
    mom_1m  = d["mom_1m"] or 0
    rng     = d["range_pct"] or 50

    # For calls: need positive momentum + near annual high
    # For puts: need negative momentum + near annual low
    is_call = mom_1m >= 3 and rng >= 55
    is_put  = mom_1m <= -3 and rng <= 45

    if not is_call and not is_put:
        return None

    # IV rank < 55: options not too expensive to buy
    if iv_rank > 60:
        return None

    # Avoid earnings within 14 days
    # (unless you specifically want an earnings play —
    # that's a different strategy not covered here)
    if d["earnings_days"] and d["earnings_days"] < 14:
        return None

    # Need some options liquidity
    if d["options_vol"] and d["options_vol"] < 200:
        return None

    direction = "Call" if is_call else "Put"

    # Suggest slightly OTM strike (best risk/reward for directional plays)
    if direction == "Call":
        strike = round(price * 1.03, 0)   # 3% OTM call
    else:
        strike = round(price * 0.97, 0)   # 3% OTM put

    # Rough premium estimate (OTM option, ~14-21 DTE)
    # Using Black-Scholes approximation: premium ≈ 0.4 × IV × price × √(T/252)
    T = 21 / 252
    est_premium_per_share = round(0.4 * (iv / 100) * price * np.sqrt(T), 2)
    est_premium_per_share = max(est_premium_per_share, 0.50)
    est_cost_contract     = round(est_premium_per_share * 100, 0)

    # How many contracts for £700 budget
    budget_gbp   = 700
    budget_usd   = budget_gbp * GBPUSD
    contracts    = max(1, int(budget_usd / est_cost_contract))
    # Cap at 5 — diversification
    contracts    = min(contracts, 5)

    # Score the idea
    score = 0
    score += min(30, abs(mom_1m) * 2)            # momentum (max 30pts)
    score += min(30, (rng - 50) * 1.5) if is_call else min(30, (50 - rng) * 1.5)
    score += (55 - iv_rank) * 0.4                # cheap IV bonus (max ~22pts)
    if d["options_vol"] and d["options_vol"] > 2000:
        score += 15
    if sector_strong:
        score += 10                              # sector tailwind

    return {
        "type":            "growth",
        "direction":       direction,
        "ticker":          d["ticker"],
        "name":            d["name"],
        "sector":          d["sector"],
        "market":          d["market"],
        "price":           price,
        "iv":              iv,
        "iv_rank_proxy":   iv_rank,
        "hv30":            d["hv30"],
        "range_pct":       rng,
        "mom_1m":          mom_1m,
        "earnings":        d["earnings"],
        "earnings_days":   d["earnings_days"],
        "options_vol":     d["options_vol"],
        "strike":          strike,
        "direction":       direction,
        "est_cost":        est_cost_contract,
        "contracts":       contracts,
        "score":           round(score, 0),
        "strategy":        f"Buy ${strike:.0f} {direction} (21 DTE)",
    }


@st.cache_data(ttl=300)
def fetch_all_candidates():
    """
    Scan all stocks in STOCK_UNIVERSE and return
    income and growth candidates sorted by score.
    """
    income_candidates  = []
    growth_candidates  = []

    for ticker in STOCK_UNIVERSE:
        d = fetch_stock_data(ticker)
        if not d:
            continue

        income = generate_income_idea(d, "neutral")
        if income:
            income_candidates.append(income)

        growth = generate_growth_idea(d, "neutral")
        if growth:
            growth_candidates.append(growth)

        time.sleep(0.2)

    income_candidates.sort(key=lambda x: x["score"], reverse=True)
    growth_candidates.sort(key=lambda x: x["score"], reverse=True)
    return income_candidates[:8], growth_candidates[:8]


@st.cache_data(ttl=600)
def fetch_all_etf_returns(tickers):
    """Batch fetch returns for all ETFs."""
    all_t = list(set(tickers + ["SPY"]))
    try:
        # Daily for 3D/1W/1M/3M
        raw = yf.download(all_t, period="6mo", interval="1d",
                          auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            closes = raw["Close"]
        else:
            closes = raw
        if hasattr(closes.index, "tz") and closes.index.tz:
            closes.index = closes.index.tz_localize(None)

        # Intraday for 1D (today vs yesterday's close)
        intra = yf.download(all_t, period="5d", interval="5m",
                            auto_adjust=True, progress=False)
        if isinstance(intra.columns, pd.MultiIndex):
            intra_c = intra["Close"]
        else:
            intra_c = intra
        if hasattr(intra_c.index, "tz") and intra_c.index.tz:
            intra_c.index = intra_c.index.tz_localize(None)

        today     = pd.Timestamp.now().normalize()
        yesterday = today - pd.tseries.offsets.BDay(1)

        def safe_ret(series, n):
            s = series.dropna()
            return round((float(s.iloc[-1]) / float(s.iloc[-n]) - 1) * 100, 2) if len(s) >= n else None

        def live_1d(ticker):
            if intra_c.empty or ticker not in intra_c.columns:
                return None
            s = intra_c[ticker].dropna()
            if s.empty:
                return None
            latest  = float(s.iloc[-1])
            prev    = s[s.index.normalize() <= yesterday]
            if prev.empty:
                return None
            return round((latest / float(prev.iloc[-1]) - 1) * 100, 2)

        spy_1m = safe_ret(closes["SPY"], 21) if "SPY" in closes.columns else None

        results = {}
        for t in tickers:
            if t not in closes.columns:
                continue
            r1m = safe_ret(closes[t], 21)
            results[t] = {
                "ret_1d":    live_1d(t),
                "ret_3d":    safe_ret(closes[t], 3),
                "ret_1w":    safe_ret(closes[t], 5),
                "ret_1m":    r1m,
                "ret_3m":    safe_ret(closes[t], 63),
                "rs_vs_spy": round(r1m - spy_1m, 2) if r1m and spy_1m else None,
            }
        return results
    except Exception:
        return {}


@st.cache_data(ttl=86400)
def fetch_holdings(etf_ticker, fmp_key=""):
    """Fetch ETF holdings from stockanalysis.com or FMP."""
    try:
        url  = f"https://stockanalysis.com/etf/{etf_ticker.lower()}/holdings/"
        hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r    = requests.get(url, headers=hdrs, timeout=12)
        if r.status_code == 200:
            tables = pd.read_html(r.text)
            if tables:
                df = tables[0].head(15).copy()
                col_map = {}
                for c in df.columns:
                    cl = str(c).lower()
                    if "symbol" in cl or "ticker" in cl: col_map[c] = "Ticker"
                    elif "name" in cl or "company" in cl: col_map[c] = "Name"
                    elif "weight" in cl or cl == "%": col_map[c] = "Weight %"
                df = df.rename(columns=col_map)
                keep = [c for c in ["Ticker","Name","Weight %"] if c in df.columns]
                if "Ticker" in keep:
                    df = df[keep]
                    if "Weight %" in df.columns:
                        df["Weight %"] = (pd.to_numeric(
                            df["Weight %"].astype(str).str.replace("%","",regex=False).str.strip(),
                            errors="coerce"
                        ).round(2))
                        df = df.sort_values("Weight %", ascending=False)
                    df["Source"] = "🟢 Live"
                    return df.reset_index(drop=True)
    except Exception:
        pass

    if fmp_key:
        try:
            url  = f"https://financialmodelingprep.com/api/v3/etf-holder/{etf_ticker}?apikey={fmp_key}"
            r    = requests.get(url, timeout=10).json()
            if isinstance(r, list) and r:
                df = pd.DataFrame(r[:15]).rename(columns={
                    "asset":"Ticker","weightPercentage":"Weight %","name":"Name"})
                df["Weight %"] = pd.to_numeric(df.get("Weight %",0), errors="coerce").round(2)
                cols = [c for c in ["Ticker","Name","Weight %"] if c in df.columns]
                df = df[cols].sort_values("Weight %", ascending=False).reset_index(drop=True)
                df["Source"] = "🟡 Live (FMP)"
                return df
        except Exception:
            pass

    return pd.DataFrame(columns=["Ticker","Name","Weight %"])


@st.cache_data(ttl=3600)
def calc_relative_strength(stock_tickers, etf_ticker, period="1mo"):
    """Calculate each stock's return vs the ETF."""
    all_t = list(set(stock_tickers + [etf_ticker]))
    try:
        raw    = yf.download(all_t, period=period, auto_adjust=True, progress=False)
        closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        rets   = ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100).round(2)
        etf_r  = float(rets.get(etf_ticker, 0))
        rows   = []
        for t in stock_tickers:
            sr = rets.get(t)
            if sr is not None:
                vs = round(float(sr) - etf_r, 2)
                rows.append({
                    "Ticker":   t,
                    f"Ret ({period}) %": round(float(sr), 2),
                    "ETF Ret %": round(etf_r, 2),
                    "vs ETF %": vs,
                    "Status":   "✅ Leading" if vs > 0 else "⚠️ Lagging",
                })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


# ============================================================
# UI HELPERS
# ============================================================

def color_range_cell(val):
    if val is None: return ""
    if val >= 60:  return "background-color:#bbf7d0"
    if val >= 35:  return "background-color:#fef08a"
    return "background-color:#fecaca"


def render_trade_card(idea, regime_bias):
    """Render one trade idea as a styled expander card."""
    if not idea:
        return

    ticker    = idea["ticker"]
    name      = idea["name"]
    sector    = idea["sector"]
    market    = idea["market"]
    price     = idea["price"]
    iv        = idea["iv"]
    iv_rank   = idea["iv_rank_proxy"]
    hv30      = idea["hv30"]
    mom_1m    = idea["mom_1m"]
    rng       = idea["range_pct"]
    earnings  = idea["earnings"]
    earn_days = idea["earnings_days"]
    opt_vol   = idea["options_vol"]
    strategy  = idea["strategy"]
    score     = idea["score"]
    mkt_flag  = "🇬🇧" if market == "UK-ADR" else ("📊" if market == "ETF" else "🇺🇸")

    if idea["type"] == "income":
        sell_put  = idea["sell_put"]
        buy_put   = idea["buy_put"]
        premium   = idea["est_premium"]
        max_risk  = idea["max_risk_contract"]
        contracts = idea["contracts"]

        header = (
            f"💰 {mkt_flag} {ticker}  —  {name}  —  ${price:.2f}  "
            f"|  IV Rank ~{iv_rank:.0f}%  |  Score {score:.0f}  "
            f"▼ expand for trade details"
        )

        with st.expander(header, expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Strategy:** {strategy}")
                st.markdown(
                    f"**Why this is an income play:**  \n"
                    f"IV at **{iv:.1f}%** vs HV30 of **{hv30:.1f}%** — "
                    f"options are pricing in bigger moves than the stock has actually been making. "
                    f"That excess premium is what you collect. "
                    f"IV rank proxy ~**{iv_rank:.0f}%** confirms options are expensive."
                )
                st.markdown(
                    f"**Sell the ${sell_put:.0f} put, buy the ${buy_put:.0f} put.**  \n"
                    f"You collect premium upfront. As long as {ticker} stays above "
                    f"${sell_put:.0f} at expiry, you keep it all.  \n"
                    f"If it falls below ${sell_put:.0f}, your loss is capped at the "
                    f"spread width ($5) minus the premium collected."
                )

            with c2:
                st.markdown("**Trade details:**")
                st.markdown(
                    f"- Collect: ~**${premium:.0f}/contract** ({gbp(premium)})"
                )
                st.markdown(
                    f"- Max risk: ~**${max_risk:.0f}/contract** ({gbp(max_risk)})"
                )
                st.markdown(
                    f"- For £700 max risk: **{contracts} contract(s)**"
                )
                st.markdown(
                    f"- Sector: {sector} | {mkt_flag} {market}"
                )
                if earn_days:
                    colour = "🔴" if earn_days < 30 else "🟢"
                    st.markdown(
                        f"- {colour} Earnings: {earnings} ({earn_days} days away)"
                    )
                else:
                    st.markdown("- ⚪ Earnings date unknown — verify on IBKR")

                st.markdown(f"- Options volume: {opt_vol:,}" if opt_vol else "- Options volume: unknown")

            st.divider()
            st.markdown(
                "**On IBKR:** Options chain → select expiry ~21-30 days out → "
                f"Sell {ticker} ${sell_put:.0f} Put / Buy {ticker} ${buy_put:.0f} Put "
                "(bull put spread). Check the mid-price — collect at least $0.30+ to make it worthwhile."
            )

    else:  # growth
        direction = idea["direction"]
        strike    = idea["strike"]
        cost      = idea["est_cost"]
        contracts = idea["contracts"]
        emoji     = "📈" if direction == "Call" else "📉"

        header = (
            f"{emoji} {mkt_flag} {ticker}  —  {name}  —  ${price:.2f}  "
            f"|  Mom {pct(mom_1m)}  |  IV Rank ~{iv_rank:.0f}%  |  Score {score:.0f}  "
            f"▼ expand for trade details"
        )

        with st.expander(header, expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Strategy:** {strategy}")
                st.markdown(
                    f"**Why this is a growth play:**  \n"
                    f"{ticker} has moved **{pct(mom_1m)}** over the last month and sits at "
                    f"**{rng:.0f}%** of its 52-week range — "
                    f"{'near the top, momentum is strong' if rng >= 65 else 'near the bottom, bearish momentum'}.  \n"
                    f"IV rank proxy ~**{iv_rank:.0f}%** — options are "
                    f"{'reasonably priced for buying' if iv_rank < 50 else 'slightly elevated but momentum justifies it'}."
                )
                if direction == "Call":
                    st.markdown(
                        f"**Buy the ${strike:.0f} call, 21 DTE.**  \n"
                        f"You profit if {ticker} moves above ${strike:.0f} + premium paid before expiry. "
                        f"Target: 2× the premium paid. "
                        f"Stop: exit if you lose 50% of premium paid."
                    )
                else:
                    st.markdown(
                        f"**Buy the ${strike:.0f} put, 21 DTE.**  \n"
                        f"You profit if {ticker} falls below ${strike:.0f} before expiry. "
                        f"Target: 2× the premium paid. "
                        f"Stop: exit if you lose 50% of premium paid."
                    )

            with c2:
                st.markdown("**Trade details:**")
                st.markdown(
                    f"- Est. cost: ~**${cost:.0f}/contract** ({gbp(cost)})"
                )
                st.markdown(
                    f"- For £700 budget: **{contracts} contract(s)**"
                )
                st.markdown(
                    f"- Total spend: ~{gbp(cost * contracts)}"
                )
                st.markdown(
                    f"- Target exit: ~{gbp(cost * contracts * 2)} (+100%)"
                )
                st.markdown(
                    f"- Stop loss: ~{gbp(cost * contracts * 0.5)} (-50%)"
                )
                st.markdown(f"- Sector: {sector} | {mkt_flag} {market}")

                if earn_days:
                    colour = "🔴" if earn_days < 14 else "🟢"
                    st.markdown(
                        f"- {colour} Earnings: {earnings} ({earn_days} days)"
                    )
                else:
                    st.markdown("- ⚪ Earnings date unknown — verify on IBKR")

            st.divider()
            st.markdown(
                f"**On IBKR:** Options chain → select expiry ~21 days out → "
                f"Buy {ticker} ${strike:.0f} {direction}. "
                "Always check the bid/ask spread — if it's wider than $0.10, "
                "use a limit order at the mid-price."
            )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")
    fmp_key = st.text_input("FMP API Key (optional)",
                            type="password",
                            help="Free at financialmodelingprep.com — unlocks ETF holdings.")
    st.divider()
    st.markdown("**Income plays** (sell premium)")
    st.markdown("Best when: VIX elevated, stock range-bound, IV expensive")
    st.markdown("**Growth plays** (buy options)")
    st.markdown("Best when: VIX low, clear trend, IV cheap")
    st.divider()
    st.markdown("**Position sizing rule**")
    st.markdown("Max risk per trade: **£700** (2% of £35K)")
    st.markdown("Max concurrent trades: **5-7**")
    st.markdown("Never risk more than **£3,500** total in open options")
    st.divider()
    st.markdown("**IBKR tips**")
    st.markdown("• Always use limit orders at the mid-price")
    st.markdown("• Check bid/ask spread — wider than $0.15 = illiquid")
    st.markdown("• Set GTC (Good Till Cancelled) orders")
    st.markdown("• Verify earnings dates in IBKR before entering")


# ============================================================
# LOAD MACRO DATA (used everywhere)
# ============================================================

macro = fetch_macro_snapshot()
regime_label, regime_colour, regime_desc, regime_bias = detect_regime_quick(macro)

vix_data  = macro.get("VIX", {})
vix_val   = vix_data.get("price")
vix_chg   = vix_data.get("chg_1d")


# ============================================================
# ALWAYS-VISIBLE REGIME BANNER
# ============================================================

st.markdown(
    f"<div style='background:{regime_colour}22;border-left:6px solid {regime_colour};"
    f"padding:10px 16px;border-radius:6px;margin-bottom:12px'>"
    f"<b style='color:{regime_colour};font-size:1.1rem'>{regime_label}</b>"
    f" &nbsp;|&nbsp; {regime_desc}"
    f"</div>",
    unsafe_allow_html=True
)

st.title("🎯 Options Trading Dashboard")
st.caption(
    "**Workflow:** Read the regime banner → check Trade Ideas → "
    "confirm sector in ETF Screener → verify on IBKR → execute manually."
)


# ============================================================
# MAIN TABS
# ============================================================

tab_ideas, tab_macro, tab_sectors, tab_holdings, tab_options = st.tabs([
    "🎯 Trade Ideas",
    "🌍 Macro",
    "📈 ETF Sectors",
    "🔍 Holdings",
    "⚡ Options Filter",
])


# ============================================================
# TAB 1 — TRADE IDEAS
# ============================================================

with tab_ideas:
    st.subheader("🎯 Trade Ideas")
    st.caption(
        "Scans all stocks in your universe every 5 minutes. "
        "Income plays (sell premium) and growth plays (buy options) are ranked separately. "
        "**These are starting points — always verify on IBKR before trading.**"
    )

    # Regime adjustment note
    if regime_bias == "puts":
        st.error(
            "⚠️ **Regime is Risk-Off** — favour put growth plays and income plays "
            "(selling elevated premium). Be cautious on call growth plays."
        )
    elif regime_bias == "calls":
        st.success(
            "✅ **Regime is Risk-On** — call growth plays are favoured. "
            "Income plays also work well in calmer conditions."
        )
    elif regime_bias == "reduce":
        st.warning(
            "🟡 **Mixed regime** — reduce size on all trades. "
            "Prefer income plays (selling defined-risk spreads) over directional bets."
        )

    # VIX premium note
    if vix_val:
        if vix_val >= 30:
            st.info(
                f"📌 **VIX {vix_val:.0f} — options are EXPENSIVE.** "
                "This is a good environment for income plays (selling premium). "
                "For growth plays, use debit spreads rather than buying naked options "
                "to reduce the cost."
            )
        elif vix_val <= 15:
            st.info(
                f"📌 **VIX {vix_val:.0f} — options are CHEAP.** "
                "Good time to buy options (growth plays). "
                "Income plays collect less premium at low VIX — be selective."
            )

    if st.button("🔄 Scan for Trade Ideas", type="primary", key="scan_btn"):
        with st.spinner("Scanning all stocks... this takes ~60 seconds..."):
            income_list, growth_list = fetch_all_candidates()
        st.session_state["income_list"] = income_list
        st.session_state["growth_list"] = growth_list

    income_list = st.session_state.get("income_list", [])
    growth_list = st.session_state.get("growth_list", [])

    if not income_list and not growth_list:
        st.info("Click **Scan for Trade Ideas** above to find today's candidates.")
    else:
        col_inc, col_gr = st.columns(2)

        with col_inc:
            st.markdown("### 💰 Income Plays")
            st.caption(
                "Sell premium — collect money upfront. "
                "You win if the stock stays in a range. "
                "Best when IV is high and no catalyst is coming. "
                "**Strategy: put credit spreads (defined risk).**"
            )
            if income_list:
                for idea in income_list[:5]:
                    render_trade_card(idea, regime_bias)
            else:
                st.info("No strong income candidates found right now.")

        with col_gr:
            st.markdown("### 🚀 Growth Plays")
            st.caption(
                "Buy options — pay upfront, need a directional move. "
                "Calls if stock is in an uptrend, puts if in a downtrend. "
                "**Strategy: buy slightly OTM calls or puts, 21 DTE.**  \n"
                "Target 2× the premium. Stop at -50%."
            )
            if growth_list:
                for idea in growth_list[:5]:
                    render_trade_card(idea, regime_bias)
            else:
                st.info("No strong growth candidates found right now.")

        st.divider()
        st.markdown("### 📋 How to Use These on IBKR")
        with st.expander("Step-by-step guide for executing on IBKR", expanded=False):
            st.markdown("""
**For Income Plays (put credit spreads):**
1. Search the ticker in IBKR TWS or mobile app
2. Right-click → Trade → Options → Options Chain
3. Select expiry ~21-30 days out
4. Find the suggested sell strike — check the bid price
5. Find the buy strike (5 points lower) — check the ask price
6. The net credit = sell bid minus buy ask
7. If net credit < $0.30, skip — not worth the risk
8. Place as a combo order (spread) not two separate legs
9. Use a limit order at the mid-price of the spread

**For Growth Plays (buying calls or puts):**
1. Search the ticker → Options Chain
2. Select expiry ~21 days out
3. Find the suggested strike — check the ask price
4. Check bid/ask spread — if wider than $0.15, it's illiquid
5. Place a limit order at the mid-price
6. Set a target sell order at 2× what you paid
7. Set a mental stop at 50% loss — exit manually

**General rules:**
- Always verify the earnings date in IBKR before entering
- Never spend more than £700 on a single trade
- Check the option has at least 100 open interest
- If in doubt, paper trade first using IBKR's paper account
            """)


# ============================================================
# TAB 2 — MACRO
# ============================================================

with tab_macro:
    st.subheader("🌍 Macro Dashboard")
    st.caption("The macro regime drives everything else. Read this to calibrate your Trade Ideas.")

    # Key metric tiles
    tile_cols = st.columns(6)
    metrics = [
        ("VIX",             "VIX",             "Fear index. >25 = elevated. >35 = extreme."),
        ("10Y Treasury",    "10Y Yield %",      "Rising = headwind for growth stocks."),
        ("2Y Treasury",     "2Y Yield %",       "Fed expectations proxy."),
        ("US Dollar (DXY)", "Dollar (DXY)",     "Rising = headwind for commodities."),
        ("Gold",            "Gold ($)",         "Rising = safe-haven demand."),
        ("Crude Oil",       "Crude Oil ($)",    "Rising = inflation/stagflation risk."),
    ]
    for col, (key, label, tip) in zip(tile_cols, metrics):
        d = macro.get(key, {})
        with col:
            if d:
                st.metric(label,
                          f"{d['price']:.2f}",
                          delta=f"{d['chg_1d']:+.2f}%",
                          help=tip)
            else:
                st.metric(label, "N/A")

    # Yield curve spread
    y10 = macro.get("10Y Treasury", {}).get("price")
    y2  = macro.get("2Y Treasury",  {}).get("price")
    if y10 and y2:
        spread = y10 - y2
        sc1, sc2 = st.columns([1, 3])
        with sc1:
            colour = "red" if spread < 0 else ("orange" if spread < 0.3 else "green")
            st.markdown(
                f"**10Y–2Y Spread: "
                f"<span style='color:{colour}'>{spread:+.2f}%</span>**",
                unsafe_allow_html=True
            )
        with sc2:
            if spread < 0:
                st.error("⚠️ Inverted yield curve — recession signal. Avoid cyclicals. Favour quality and defensive.")
            elif spread < 0.3:
                st.warning("🟡 Flat curve — financials neutral. Prefer shorter expiries.")
            else:
                st.success("🟢 Normal curve — financials have tailwind. LEAPS viable on strong trends.")

    st.divider()

    # How to read each macro signal in context of your trading
    st.markdown("### 📖 What each signal means for your trades")
    with st.expander("VIX — Fear Index", expanded=False):
        st.markdown(f"""
**Current VIX: {vix_val:.1f}** (change today: {pct(vix_chg)})

VIX measures how much the options market expects the S&P 500 to move over the next 30 days.

| VIX Level | What it means | Your strategy |
|-----------|--------------|---------------|
| Below 15 | Very calm, low fear | Options are cheap → favour buying (growth plays) |
| 15–20 | Normal | Both strategies work → let IV rank decide |
| 20–25 | Mild concern | Slightly favour income plays, reduce growth play size |
| 25–35 | Elevated fear | Income plays preferred — premium is elevated |
| Above 35 | Extreme fear | Sell premium aggressively. Do NOT buy naked options. |

**VIX direction matters as much as the level:**
- VIX rising fast = fear accelerating → reduce all positions
- VIX falling steadily = fear draining → add growth plays
        """)

    with st.expander("HYG — High Yield Credit (the canary)", expanded=False):
        hyg = macro.get("HYG", {})
        st.markdown(f"""
**HYG today: {pct(hyg.get('chg_1d'))}**

HYG holds high-yield (junk) bonds. When companies start to struggle, their bonds fall first — before their stock prices do.

**Why it matters:**
- HYG falling while stocks hold up = warning. Stocks usually follow HYG down within days.
- HYG rising = credit markets healthy = genuine risk-on signal
- This is the single most reliable early warning signal available without a Bloomberg terminal.

**Rule of thumb:**
If HYG drops more than 1% on a day when SPY is flat or up, reduce your call positions.
        """)

    with st.expander("Yield Curve — 10Y vs 2Y", expanded=False):
        st.markdown(f"""
**Current spread: {f'{spread:+.2f}%' if y10 and y2 else 'N/A'}**

The yield curve shows the difference between what you earn lending money for 10 years vs 2 years.

**Normal curve (positive):** Longer lending = more reward = healthy economy.
→ Banks profitable → financials have tailwind → cyclicals work.

**Inverted curve (negative — 2Y yields higher than 10Y):**
This is unusual. It means the market expects rates to fall in future (i.e., expects a slowdown).
→ Historically precedes every US recession since 1970.
→ Avoid long-dated LEAPS on cyclicals. Favour quality, defence, healthcare.
→ Bank earnings squeezed (they borrow short, lend long — inverted curve = their margin shrinks).
        """)

    with st.expander("Dollar (DXY) — Who it helps and hurts", expanded=False):
        dxy = macro.get("US Dollar (DXY)", {})
        st.markdown(f"""
**DXY today: {pct(dxy.get('chg_1d'))}**

The dollar index measures USD strength vs a basket of currencies (EUR, JPY, GBP, CAD, SEK, CHF).

**Dollar RISING hurts:**
- Commodities (oil, gold, copper — priced in USD, more expensive for foreign buyers)
- Emerging markets (they have USD-denominated debt)
- US multinationals (overseas earnings worth less when converted back to USD)
- Sectors: XLE, GDX, SIL, EEM, KWEB

**Dollar RISING helps:**
- Domestic US companies (mostly domestic revenue)
- UK companies reporting in GBP (their USD earnings buy more pounds)
- Sectors: XLP, XLV, XLF (domestic focus)

**Dollar FALLING — reverse of the above.**
GLD, XLE, KWEB, EEM all get a tailwind from a weaker dollar.
        """)


# ============================================================
# TAB 3 — ETF SECTORS
# ============================================================

with tab_sectors:
    st.subheader("📈 ETF Sector Screener")
    st.caption(
        "Identifies which subsectors are moving. "
        "Use this to confirm the sector behind a Trade Idea, "
        "or to find new sectors to drill into."
    )

    all_tickers = list(dict.fromkeys(
        t for etfs in ETF_SECTORS.values() for t, _ in etfs
    ))

    sel_sectors = st.multiselect(
        "Sectors to show",
        list(ETF_SECTORS.keys()),
        default=list(ETF_SECTORS.keys()),
    )
    custom_input = st.text_input(
        "Add custom tickers (comma separated)",
        placeholder="e.g. ARKK, MSOS",
        key="custom_tickers",
    )
    custom_tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()] if custom_input else []

    if st.button("🔄 Load Sector Data", key="load_sectors"):
        with st.spinner("Fetching all ETF data..."):
            returns_data = fetch_all_etf_returns(all_tickers + custom_tickers)
        st.session_state["returns_data"] = returns_data
        st.session_state["sectors_loaded"] = True

    if not st.session_state.get("sectors_loaded"):
        st.info("Click **Load Sector Data** to populate the heatmap and tables.")
    else:
        returns_data = st.session_state.get("returns_data", {})

        # ── Heatmap ───────────────────────────────────────────
        st.markdown("### Sector Rotation Heatmap")
        st.caption(
            "Read left to right: green across all columns = accelerating. "
            "Green on right but red on left = recovering. "
            "Red on right but green on left = may be topping. "
            "The most actionable plays have green across ALL columns."
        )
        hm_rows = []
        for sector, etfs in ETF_SECTORS.items():
            if sector not in sel_sectors:
                continue
            for ticker, _ in etfs:
                if ticker in returns_data:
                    d = returns_data[ticker]
                    hm_rows.append({
                        "Sector": sector, "Ticker": ticker,
                        "1D %":  d.get("ret_1d"),  "3D %":  d.get("ret_3d"),
                        "1W %":  d.get("ret_1w"),  "1M %":  d.get("ret_1m"),
                        "3M %":  d.get("ret_3m"),  "RS vs SPY": d.get("rs_vs_spy"),
                    })

        if hm_rows:
            hm_df    = pd.DataFrame(hm_rows)
            num_cols = ["1D %","3D %","1W %","1M %","3M %","RS vs SPY"]
            def _hm(val):
                if pd.isna(val): return ""
                if val >= 5:   return "background-color:#166534;color:white"
                if val >= 2:   return "background-color:#bbf7d0"
                if val >= -2:  return "background-color:#fef08a"
                if val >= -5:  return "background-color:#fecaca"
                return "background-color:#991b1b;color:white"
            st.dataframe(
                hm_df.style.map(_hm, subset=num_cols)
                .format({c: "{:+.1f}%" for c in num_cols}, na_rep="N/A"),
                use_container_width=True, hide_index=True, height=400,
            )

        st.divider()

        # ── Calls / Puts panels ───────────────────────────────
        st.markdown("### Best Sectors for Calls vs Puts")
        all_rows = []
        for sector in sel_sectors:
            for ticker, name in ETF_SECTORS.get(sector, []):
                d = returns_data.get(ticker, {})
                rng = None
                try:
                    t    = yf.Ticker(ticker)
                    info = t.info
                    p    = safe_float(info.get("regularMarketPrice") or info.get("currentPrice"))
                    lo   = safe_float(info.get("fiftyTwoWeekLow"))
                    hi   = safe_float(info.get("fiftyTwoWeekHigh"))
                    if p and lo and hi and hi != lo:
                        rng = round((p - lo) / (hi - lo) * 100, 1)
                except Exception:
                    pass
                all_rows.append({
                    "Sector":    sector,
                    "Ticker":    ticker,
                    "1M %":      d.get("ret_1m"),
                    "RS vs SPY": d.get("rs_vs_spy"),
                    "52W %":     rng,
                })

        if all_rows:
            all_df = pd.DataFrame(all_rows)
            calls_df = all_df[
                (all_df["52W %"].fillna(0) >= 60) &
                (all_df["RS vs SPY"].fillna(-99) >= 0)
            ].sort_values("RS vs SPY", ascending=False).head(5)

            puts_df = all_df[
                (all_df["52W %"].fillna(100) <= 40) &
                (all_df["RS vs SPY"].fillna(0) <= 0)
            ].sort_values("RS vs SPY", ascending=True).head(5)

            cc, cp = st.columns(2)
            with cc:
                st.markdown("**📈 Strongest — drill into these for call ideas**")
                if not calls_df.empty:
                    for _, r in calls_df.iterrows():
                        with st.expander(
                            f"{r['Ticker']}  —  {r['Sector']}  "
                            f"|  52W {r['52W %']:.0f}%  |  RS {pct(r['RS vs SPY'])}  ▼",
                            expanded=False,
                        ):
                            st.markdown(f"**Drill into holdings** → Holdings tab")
                            h = fetch_holdings(r["Ticker"], fmp_key)
                            if not h.empty:
                                rs = calc_relative_strength(
                                    h["Ticker"].tolist(), r["Ticker"], "1mo"
                                )
                                if not rs.empty:
                                    h = h.merge(rs[["Ticker","vs ETF %","Status"]], on="Ticker", how="left")
                                def _hl(row):
                                    s = [""] * len(row)
                                    if "Status" in row.index:
                                        i = list(row.index).index("Status")
                                        s[i] = "background-color:#bbf7d0" if row["Status"] == "✅ Leading" else ("background-color:#fecaca" if row["Status"] == "⚠️ Lagging" else "")
                                    return s
                                st.dataframe(h.style.apply(_hl, axis=1), use_container_width=True, hide_index=True)
                                leading = h[h.get("Status","") == "✅ Leading"]["Ticker"].tolist() if "Status" in h.columns else []
                                if leading:
                                    st.success(f"Leading: {', '.join(leading)}")
                                    st.text_input("Copy to Options Filter:", ", ".join(leading), key=f"copy_c_{r['Ticker']}")
                            else:
                                st.link_button(f"Look up {r['Ticker']} holdings",
                                               f"https://stockanalysis.com/etf/{r['Ticker'].lower()}/holdings/")
                else:
                    st.info("No strong call sectors right now.")

            with cp:
                st.markdown("**📉 Weakest — drill into these for put ideas**")
                if not puts_df.empty:
                    for _, r in puts_df.iterrows():
                        with st.expander(
                            f"{r['Ticker']}  —  {r['Sector']}  "
                            f"|  52W {r['52W %']:.0f}%  |  RS {pct(r['RS vs SPY'])}  ▼",
                            expanded=False,
                        ):
                            h = fetch_holdings(r["Ticker"], fmp_key)
                            if not h.empty:
                                rs = calc_relative_strength(
                                    h["Ticker"].tolist(), r["Ticker"], "1mo"
                                )
                                if not rs.empty:
                                    h = h.merge(rs[["Ticker","vs ETF %","Status"]], on="Ticker", how="left")
                                def _hl2(row):
                                    s = [""] * len(row)
                                    if "Status" in row.index:
                                        i = list(row.index).index("Status")
                                        s[i] = "background-color:#bbf7d0" if row["Status"] == "✅ Leading" else ("background-color:#fecaca" if row["Status"] == "⚠️ Lagging" else "")
                                    return s
                                st.dataframe(h.style.apply(_hl2, axis=1), use_container_width=True, hide_index=True)
                                lagging = h[h.get("Status","") == "⚠️ Lagging"]["Ticker"].tolist() if "Status" in h.columns else []
                                if lagging:
                                    st.error(f"Put candidates: {', '.join(lagging)}")
                                    st.text_input("Copy to Options Filter:", ", ".join(lagging), key=f"copy_p_{r['Ticker']}")
                            else:
                                st.link_button(f"Look up {r['Ticker']} holdings",
                                               f"https://stockanalysis.com/etf/{r['Ticker'].lower()}/holdings/")
                else:
                    st.info("No weak put sectors right now.")


# ============================================================
# TAB 4 — HOLDINGS DRILL DOWN
# ============================================================

with tab_holdings:
    st.subheader("🔍 Holdings Drill-Down")
    st.caption(
        "Pick any ETF to see its top holdings, "
        "and which stocks are leading vs lagging the ETF. "
        "Leading stocks = call candidates. Lagging stocks = put candidates."
    )

    hcol1, hcol2 = st.columns(2)
    with hcol1:
        sector_choice = st.selectbox("Sector", list(ETF_SECTORS.keys()), key="h_sector")
    with hcol2:
        etf_labels = [f"{t}  —  {n}" for t, n in ETF_SECTORS[sector_choice]]
        etf_choice = st.selectbox("ETF", etf_labels, key="h_etf")
        etf_ticker = etf_choice.split("  —  ")[0].strip()

    period = st.radio("Comparison period", ["1wk","1mo","3mo"], index=1, horizontal=True)

    if st.button("🔍 Drill Down", key="drill_btn"):
        with st.spinner(f"Fetching {etf_ticker} holdings..."):
            holdings = fetch_holdings(etf_ticker, fmp_key)

        if holdings.empty:
            st.error(f"Could not fetch holdings for {etf_ticker}")
            c1, c2 = st.columns(2)
            with c1:
                st.link_button(f"stockanalysis.com — {etf_ticker}",
                               f"https://stockanalysis.com/etf/{etf_ticker.lower()}/holdings/")
            with c2:
                st.link_button(f"ETF Database — {etf_ticker}",
                               f"https://etfdb.com/etf/{etf_ticker}/#holdings")
        else:
            tickers_list = holdings["Ticker"].tolist()
            with st.spinner("Calculating relative strength..."):
                rs_df = calc_relative_strength(tickers_list, etf_ticker, period=period)

            if not rs_df.empty:
                merged = holdings.merge(
                    rs_df[["Ticker", f"Ret ({period}) %", "vs ETF %", "Status"]],
                    on="Ticker", how="left"
                )
            else:
                merged = holdings.copy()

            def _hl_h(row):
                styles = [""] * len(row)
                if "Status" in row.index:
                    i = list(row.index).index("Status")
                    if row["Status"] == "✅ Leading":
                        styles[i] = "background-color:#bbf7d0"
                    elif row["Status"] == "⚠️ Lagging":
                        styles[i] = "background-color:#fecaca"
                return styles

            st.dataframe(merged.style.apply(_hl_h, axis=1),
                         use_container_width=True, hide_index=True)

            if not rs_df.empty:
                fig = px.bar(
                    rs_df.sort_values("vs ETF %"),
                    x="vs ETF %", y="Ticker", orientation="h",
                    color="vs ETF %",
                    color_continuous_scale=["#dc2626","#fef08a","#16a34a"],
                    text="vs ETF %", height=max(300, len(rs_df) * 35),
                )
                fig.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
                fig.add_vline(x=0, line_dash="dash", line_color="gray")
                fig.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            leading = merged[merged.get("Status","") == "✅ Leading"]["Ticker"].tolist() if "Status" in merged.columns else tickers_list
            lagging = merged[merged.get("Status","") == "⚠️ Lagging"]["Ticker"].tolist() if "Status" in merged.columns else []

            col_l, col_r = st.columns(2)
            with col_l:
                if leading:
                    st.success(f"**Call candidates (leading):** {', '.join(leading)}")
                    st.text_input("Copy to Options Filter:", ", ".join(leading), key="copy_leading")
            with col_r:
                if lagging:
                    st.error(f"**Put candidates (lagging):** {', '.join(lagging)}")
                    st.text_input("Copy to Options Filter:", ", ".join(lagging), key="copy_lagging")


# ============================================================
# TAB 5 — OPTIONS FILTER
# ============================================================

with tab_options:
    st.subheader("⚡ Options Filter")
    st.caption(
        "Paste tickers from the Holdings tab or Trade Ideas. "
        "Checks IV, HV30, earnings date, and gives a signal for each stock."
    )

    ticker_input = st.text_input(
        "Tickers (comma separated)",
        placeholder="e.g. NVDA, AMD, AVGO, TSM",
        key="opt_tickers",
    )

    if st.button("⚡ Analyse", key="opt_btn") and ticker_input:
        raw_tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

        with st.spinner(f"Fetching options data for {', '.join(raw_tickers)}..."):
            results = []
            for ticker in raw_tickers:
                d = fetch_stock_data(ticker)
                if d:
                    # Signal
                    iv, hv30 = d["iv"], d["hv30"]
                    if iv and hv30:
                        ratio = iv / hv30
                        if ratio > 1.2:   sig = "🔴 Sell Premium (expensive)"
                        elif ratio < 0.8: sig = "🟢 Buy Options (cheap)"
                        else:             sig = "🟡 Fair Value"
                    else:
                        sig = "⚪ N/A"

                    results.append({
                        "Ticker":        ticker,
                        "Price":         f"${d['price']:.2f}" if d["price"] else "N/A",
                        "IV %":          d["iv"],
                        "HV30 %":        d["hv30"],
                        "IV/HV":         round(d["iv"]/d["hv30"],2) if d["iv"] and d["hv30"] else None,
                        "Signal":        sig,
                        "IV Rank ~":     f"~{d['iv_rank_proxy']:.0f}%" if d["iv_rank_proxy"] else "N/A",
                        "Options Vol":   d["options_vol"],
                        "Next Earnings": d["earnings"] or "⚠️ Check manually",
                        "Days to Earn":  d["earnings_days"],
                    })
                time.sleep(0.2)

        if results:
            df = pd.DataFrame(results)

            def _style_opts(row):
                styles = [""] * len(row)
                if "Signal" in row.index:
                    i = list(row.index).index("Signal")
                    sig = str(row["Signal"])
                    if "Sell"  in sig: styles[i] = "background-color:#fecaca"
                    elif "Buy" in sig: styles[i] = "background-color:#bbf7d0"
                    elif "Fair" in sig: styles[i] = "background-color:#fef08a"
                return styles

            st.dataframe(df.style.apply(_style_opts, axis=1),
                         use_container_width=True, hide_index=True)

            # Earnings warnings
            st.markdown("#### ⚠️ Earnings Risk")
            warned = False
            for r in results:
                days = r["Days to Earn"]
                earn = r["Next Earnings"]
                if "Check" in str(earn):
                    st.error(f"**{r['Ticker']}** — earnings date unknown. Check on IBKR before trading.")
                    warned = True
                elif days is not None:
                    if 0 <= days <= 14:
                        st.error(f"**{r['Ticker']}** — earnings in {days} days ({earn}). Very high risk. Avoid unless trading earnings specifically.")
                        warned = True
                    elif days <= 21:
                        st.warning(f"**{r['Ticker']}** — earnings in {days} days ({earn}). IV will spike into date.")
                        warned = True
                    else:
                        st.success(f"**{r['Ticker']}** — earnings {days} days away ({earn}). Safe to trade. ✅")
                        warned = True
            if not warned:
                st.success("No earnings concerns for the tickers checked.")

            # Summary
            st.markdown("#### 🎯 Summary")
            sell_list = [r["Ticker"] for r in results if "Sell" in r["Signal"]]
            buy_list  = [r["Ticker"] for r in results if "Buy"  in r["Signal"]]
            sc1, sc2  = st.columns(2)
            with sc1:
                if buy_list:
                    st.success(f"**Buy options (cheap IV):** {', '.join(buy_list)}")
            with sc2:
                if sell_list:
                    st.info(f"**Sell premium (expensive IV):** {', '.join(sell_list)}")

            st.divider()
            st.markdown(
                "**Next step:** Take your chosen ticker to IBKR. "
                "Check the live options chain — use these signals as a guide, "
                "not an instruction. Always verify the IV rank in IBKR's "
                "options analytics before placing the trade."
            )
