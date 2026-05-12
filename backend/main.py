from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

app = FastAPI(title="台股篩選器 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=10)

# 台股主要成分股清單（上市公司）
TAIWAN_STOCKS = [
    "2330", "2317", "2454", "2308", "2382", "2881", "2303", "2882",
    "2412", "2886", "2884", "2891", "6505", "2885", "1303", "1301",
    "2883", "2887", "2892", "2890", "1326", "2002", "3711", "2207",
    "5880", "2395", "3034", "2408", "2357", "4904", "2327", "3008",
    "2379", "2345", "2353", "2356", "3045", "4938", "2337", "6669",
    "3231", "2371", "2376", "2324", "2344", "2360", "2385", "2388",
    "2409", "2458", "2464", "2474", "2492", "2498", "2542", "2545",
    "2603", "2609", "2615", "2618", "2633", "2634", "2637", "2641",
    "2801", "2823", "2834", "2836", "2838", "2845", "2849", "2855",
    "2867", "2880", "2888", "2889", "2893", "2897", "2912", "2915",
    "3006", "3017", "3019", "3022", "3023", "3024", "3025", "3026",
    "3027", "3029", "3030", "3035", "3036", "3037", "3038", "3041",
    "3042", "3044", "3046", "3047", "3048", "3049", "3050", "3051",
    "1101", "1102", "1216", "1402", "2105", "2201", "2204", "2474",
    "6415", "6488", "6770", "8046", "8詣", "912", "3704", "6278",
    "4958", "5215", "6239", "6257", "6269", "6271", "6272", "6274",
]

# 移除重複並只保留有效股票代碼
TAIWAN_STOCKS = list(set([s for s in TAIWAN_STOCKS if s.isdigit() and len(s) == 4]))
TAIWAN_STOCKS.sort()

class FilterCondition(BaseModel):
    ma1: int
    operator: str  # gt, lt, gte, lte, eq
    ma2: int
    period: str = "1d"  # 1d, 1wk, 1mo

class ScreenerRequest(BaseModel):
    conditions: List[FilterCondition]

class StockResult(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: int
    ma_values: dict


def get_operator_func(op: str):
    ops = {
        "gt": lambda a, b: a > b,
        "lt": lambda a, b: a < b,
        "gte": lambda a, b: a >= b,
        "lte": lambda a, b: a <= b,
        "eq": lambda a, b: abs(a - b) / b < 0.001 if b != 0 else False,
    }
    return ops.get(op)


def fetch_stock_data(symbol: str, period_map: dict):
    """Fetch stock data for a single symbol"""
    ticker_symbol = f"{symbol}.TW"
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        results = {}
        for period, interval in period_map.items():
            if period == "1d":
                hist = ticker.history(period="6mo", interval="1d")
            elif period == "1wk":
                hist = ticker.history(period="2y", interval="1wk")
            elif period == "1mo":
                hist = ticker.history(period="5y", interval="1mo")
            else:
                hist = ticker.history(period="6mo", interval="1d")

            if hist.empty or len(hist) < 5:
                return None

            results[period] = hist

        # Get current price info
        if "1d" in results:
            hist_1d = results["1d"]
            current_price = float(hist_1d["Close"].iloc[-1])
            prev_price = float(hist_1d["Close"].iloc[-2]) if len(hist_1d) > 1 else current_price
            change = current_price - prev_price
            change_pct = (change / prev_price * 100) if prev_price != 0 else 0
            volume = int(hist_1d["Volume"].iloc[-1])
        else:
            return None

        name = info.get("longName", info.get("shortName", symbol))
        # Shorten name for display
        if name and len(name) > 20:
            name = name[:20]

        return {
            "symbol": symbol,
            "name": name,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": volume,
            "hist_data": results,
        }
    except Exception as e:
        return None


def calculate_ma(hist: pd.DataFrame, period: int) -> Optional[float]:
    if hist is None or len(hist) < period:
        return None
    ma = hist["Close"].rolling(window=period).mean().iloc[-1]
    if pd.isna(ma):
        return None
    return float(ma)


def check_conditions(stock_data: dict, conditions: List[FilterCondition]) -> tuple[bool, dict]:
    ma_values = {}
    hist_data = stock_data["hist_data"]

    for cond in conditions:
        period = cond.period
        hist = hist_data.get(period)
        if hist is None:
            return False, {}

        ma1_val = calculate_ma(hist, cond.ma1)
        ma2_val = calculate_ma(hist, cond.ma2)

        if ma1_val is None or ma2_val is None:
            return False, {}

        op_func = get_operator_func(cond.operator)
        if not op_func or not op_func(ma1_val, ma2_val):
            return False, {}

        period_key = period
        if period_key not in ma_values:
            ma_values[period_key] = {}
        ma_values[period_key][f"MA{cond.ma1}"] = round(ma1_val, 2)
        ma_values[period_key][f"MA{cond.ma2}"] = round(ma2_val, 2)

    return True, ma_values


@app.get("/")
def root():
    return {"message": "台股篩選器 API 運行中"}


@app.get("/api/stocks")
def get_stock_list():
    """Return the list of tracked stocks"""
    return {"stocks": TAIWAN_STOCKS, "count": len(TAIWAN_STOCKS)}


@app.post("/api/screen")
async def screen_stocks(request: ScreenerRequest):
    """Screen stocks based on MA conditions"""
    if not request.conditions:
        raise HTTPException(status_code=400, detail="請至少設定一個篩選條件")

    # Determine which periods we need
    needed_periods = set()
    for cond in request.conditions:
        needed_periods.add(cond.period)
    period_map = {p: p for p in needed_periods}

    results = []
    errors = []

    # Fetch data concurrently
    loop = asyncio.get_event_loop()

    async def process_stock(symbol):
        try:
            stock_data = await loop.run_in_executor(
                executor, fetch_stock_data, symbol, period_map
            )
            if stock_data is None:
                return None

            passed, ma_values = check_conditions(stock_data, request.conditions)
            if passed:
                return {
                    "symbol": stock_data["symbol"],
                    "name": stock_data["name"],
                    "price": stock_data["price"],
                    "change": stock_data["change"],
                    "change_pct": stock_data["change_pct"],
                    "volume": stock_data["volume"],
                    "ma_values": ma_values,
                }
        except Exception as e:
            return None
        return None

    tasks = [process_stock(symbol) for symbol in TAIWAN_STOCKS]
    batch_results = await asyncio.gather(*tasks)

    results = [r for r in batch_results if r is not None]

    # Sort by volume descending
    results.sort(key=lambda x: x["volume"], reverse=True)

    return {
        "results": results,
        "count": len(results),
        "total_screened": len(TAIWAN_STOCKS),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/stock/{symbol}")
async def get_stock_detail(symbol: str):
    """Get detailed data for a single stock"""
    loop = asyncio.get_event_loop()
    period_map = {"1d": "1d", "1wk": "1wk", "1mo": "1mo"}
    stock_data = await loop.run_in_executor(
        executor, fetch_stock_data, symbol, period_map
    )

    if not stock_data:
        raise HTTPException(status_code=404, detail=f"找不到股票 {symbol}")

    # Return OHLCV for chart
    hist = stock_data["hist_data"].get("1d", pd.DataFrame())
    chart_data = []
    if not hist.empty:
        for idx, row in hist.tail(120).iterrows():
            chart_data.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

    return {
        "symbol": stock_data["symbol"],
        "name": stock_data["name"],
        "price": stock_data["price"],
        "change": stock_data["change"],
        "change_pct": stock_data["change_pct"],
        "volume": stock_data["volume"],
        "chart_data": chart_data,
    }
