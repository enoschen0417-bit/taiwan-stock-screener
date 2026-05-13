from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="台股篩選器 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=20)

TAIWAN_STOCKS_RAW = [
    "2330","2303","2308","2317","2327","2337","2344","2345","2353","2354",
    "2356","2357","2358","2360","2362","2363","2364","2365","2367","2368",
    "2369","2371","2373","2374","2375","2376","2377","2379","2380","2382",
    "2383","2384","2385","2387","2388","2390","2392","2393","2395","2396",
    "2397","2399","2401","2404","2405","2406","2408","2409","2412","2414",
    "2415","2417","2420","2421","2423","2424","2425","2426","2428","2429",
    "2430","2431","2432","2433","2434","2436","2438","2439","2440","2441",
    "2442","2443","2444","2445","2448","2450","2451","2452","2453","2454",
    "2455","2456","2457","2458","2459","2460","2461","2462","2463","2464",
    "2465","2466","2467","2468","2469","2470","2471","2472","2473","2474",
    "2475","2476","2477","2478","2480","2481","2482","2483","2484","2485",
    "2486","2488","2489","2490","2491","2492","2493","2495","2496","2497",
    "2498","2499",
    "3008","3009","3010","3011","3012","3013","3014","3015","3016","3017",
    "3018","3019","3020","3021","3022","3023","3024","3025","3026","3027",
    "3028","3029","3030","3031","3032","3033","3034","3035","3036","3037",
    "3038","3039","3040","3041","3042","3044","3045","3046","3047","3048",
    "3049","3050","3051","3052","3053","3054","3055","3056","3057","3058",
    "3059","3060","3061","3062","3063","3064","3065","3066","3067","3068",
    "3069","3070","3071","3072","3073","3074","3075","3076","3077",
    "2880","2881","2882","2883","2884","2885","2886","2887","2888","2889",
    "2890","2891","2892","2893","2897","2801","2823","2834","2836","2838",
    "2845","2849","2855","2867","5880","5876","5884","5885","5886",
    "2841","2847","2851","2852","2854","2856","2860","2863","2864",
    "1101","1102","1103","1104","1108","1109","1201","1210","1213","1215",
    "1216","1217","1218","1219","1220","1225","1227","1229","1231","1232",
    "1233","1234","1235","1236","1256","1301","1303","1304","1305","1307",
    "1308","1309","1310","1312","1313","1314","1315","1316","1317","1319",
    "1321","1323","1324","1325","1326","1402","1410","1413","1414","1416",
    "1417","1418","1419","1423","1424","1425","1426","1429",
    "2002","2006","2007","2008","2010","2011","2012","2013","2014","2015",
    "2016","2017","2018","2019","2020","2021","2022","2023","2024","2025",
    "2027","2028","2029","2030","2031","2032","2033","2034","2035","2038",
    "2040","2041","2042","2043","2044","2045","2046","2049","2050","2059",
    "2201","2204","2207","2208","2209","2211","2212","2213","2214",
    "4904","4905",
    "2603","2605","2606","2607","2608","2609","2610","2611","2612","2613",
    "2615","2616","2617","2618","2619","2620","2621","2623","2624","2626",
    "2627","2628","2629","2630","2633","2634","2637","2641",
    "2501","2504","2505","2506","2507","2509","2511","2514","2515","2516",
    "2520","2524","2527","2528","2530","2534","2535","2536","2537","2538",
    "2539","2540","2542","2543","2545","2546","2547","2548","2597",
    "2905","2906","2907","2908","2910","2911","2912","2913","2914","2915",
    "2923","2924","2925","2926","2929","2930","9902","9904","9907",
    "1726","1730","1731","4166","4174","4175","4176","4180","4182",
    "4183","4184","4185","4186","4187","4188","4189","4190","4191","4192",
    "6457","6461","6462","6463","6464","6465","6466","6467","6468","6469",
    "3704","3706","3707","3708","3709","3710","3711","3712","3714",
    "3715","3716","3717","3719","3720","3721","3722","3723","3724",
    "6239","6257","6269","6271","6272","6274","6278","6283","6285","6286",
    "6288","6289","6290","6291","6292","6293","6294","6295","6296","6297",
    "6415","6488","6505","6533","6669","6770","8046",
    "6414","6416","6417","6418","6419","6420","6421","6422","6423","6424",
    "6425","6426","6427","6428","6429","6430","6431","6432","6433","6434",
    "4958","5215","4938","3231",
]

TAIWAN_STOCKS = list(set([s for s in TAIWAN_STOCKS_RAW if s.isdigit() and len(s) == 4]))
TAIWAN_STOCKS.sort()


class FilterCondition(BaseModel):
    ma1: int
    operator: str
    ma2: int
    period: str = "1d"


class ScreenerRequest(BaseModel):
    conditions: List[FilterCondition]
    volume_filter: Optional[str] = None  # "1000_5000", "5000_10000", "10000_up"


def get_operator_func(op: str):
    ops = {
        "gt": lambda a, b: a > b,
        "lt": lambda a, b: a < b,
        "gte": lambda a, b: a >= b,
        "lte": lambda a, b: a <= b,
    }
    return ops.get(op)


def check_volume_filter(volume_shares: int, volume_filter: str) -> bool:
    lots = volume_shares / 1000  # 換算成張
    if volume_filter == "1000_5000":
        return 1000 <= lots < 5000
    elif volume_filter == "5000_10000":
        return 5000 <= lots < 10000
    elif volume_filter == "10000_up":
        return lots >= 10000
    return True


def fetch_stock_data(symbol: str, period_map: dict):
    ticker_symbol = f"{symbol}.TW"
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        results = {}
        for period in period_map:
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

        if "1d" not in results:
            return None

        hist_1d = results["1d"]
        current_price = float(hist_1d["Close"].iloc[-1])
        prev_price = float(hist_1d["Close"].iloc[-2]) if len(hist_1d) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price * 100) if prev_price != 0 else 0
        volume = int(hist_1d["Volume"].iloc[-1])

        name = info.get("longName", info.get("shortName", symbol))
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
    except Exception:
        return None


def calculate_ma(hist: pd.DataFrame, period: int) -> Optional[float]:
    if hist is None or len(hist) < period:
        return None
    ma = hist["Close"].rolling(window=period).mean().iloc[-1]
    if pd.isna(ma):
        return None
    return float(ma)


def check_ma_conditions(stock_data: dict, conditions: List[FilterCondition]):
    ma_values = {}
    hist_data = stock_data["hist_data"]
    for cond in conditions:
        hist = hist_data.get(cond.period)
        if hist is None:
            return False, {}
        ma1_val = calculate_ma(hist, cond.ma1)
        ma2_val = calculate_ma(hist, cond.ma2)
        if ma1_val is None or ma2_val is None:
            return False, {}
        op_func = get_operator_func(cond.operator)
        if not op_func or not op_func(ma1_val, ma2_val):
            return False, {}
        if cond.period not in ma_values:
            ma_values[cond.period] = {}
        ma_values[cond.period][f"MA{cond.ma1}"] = round(ma1_val, 2)
        ma_values[cond.period][f"MA{cond.ma2}"] = round(ma2_val, 2)
    return True, ma_values


@app.get("/")
def root():
    return {"message": "台股篩選器 API v2", "stocks": len(TAIWAN_STOCKS)}


@app.get("/api/stocks")
def get_stock_list():
    return {"stocks": TAIWAN_STOCKS, "count": len(TAIWAN_STOCKS)}


@app.post("/api/screen")
async def screen_stocks(request: ScreenerRequest):
    if not request.conditions:
        raise HTTPException(status_code=400, detail="請至少設定一個篩選條件")

    needed_periods = set(cond.period for cond in request.conditions)
    needed_periods.add("1d")
    period_map = {p: p for p in needed_periods}
    loop = asyncio.get_event_loop()

    async def process_stock(symbol):
        try:
            stock_data = await loop.run_in_executor(executor, fetch_stock_data, symbol, period_map)
            if stock_data is None:
                return None
            if request.volume_filter:
                if not check_volume_filter(stock_data["volume"], request.volume_filter):
                    return None
            passed, ma_values = check_ma_conditions(stock_data, request.conditions)
            if not passed:
                return None
            return {
                "symbol": stock_data["symbol"],
                "name": stock_data["name"],
                "price": stock_data["price"],
                "change": stock_data["change"],
                "change_pct": stock_data["change_pct"],
                "volume": stock_data["volume"],
                "volume_lots": round(stock_data["volume"] / 1000),
                "ma_values": ma_values,
            }
        except Exception:
            return None

    tasks = [process_stock(s) for s in TAIWAN_STOCKS]
    batch_results = await asyncio.gather(*tasks)
    results = [r for r in batch_results if r is not None]
    results.sort(key=lambda x: x["volume"], reverse=True)

    return {
        "results": results,
        "count": len(results),
        "total_screened": len(TAIWAN_STOCKS),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/stock/{symbol}")
async def get_stock_detail(symbol: str):
    loop = asyncio.get_event_loop()
    period_map = {"1d": "1d", "1wk": "1wk", "1mo": "1mo"}
    stock_data = await loop.run_in_executor(executor, fetch_stock_data, symbol, period_map)
    if not stock_data:
        raise HTTPException(status_code=404, detail=f"找不到股票 {symbol}")

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
        "volume_lots": round(stock_data["volume"] / 1000),
        "chart_data": chart_data,
    }
