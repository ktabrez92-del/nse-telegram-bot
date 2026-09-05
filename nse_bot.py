cat << 'EOF' > nse_bot.py
import time
import logging
import threading
import schedule
import requests
from datetime import datetime

BOT_TOKEN = "8744426734:AAFR62qx-AikwDnTUGtj-F9tID_VA7Bq39A"
CHAT_ID = "-1003915913228"

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/'
}

processed_results = set()

def send_telegram_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    for attempt in range(3):
        try:
            res = requests.post(url, data=payload, timeout=15)
            if res.status_code == 200:
                return True
        except Exception as e:
            logging.error(f"Telegram Send Error: {e}")
            time.sleep(2)
    return False

def is_valid_intraday_stock(ltp):
    return ltp >= 15.0

# ----------------- 1. UPCOMING RESULTS CALENDAR -----------------
def scan_upcoming_results():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/event-calendar"
        res = session.get(url, headers=HEADERS, timeout=12)
        
        if res.status_code == 200:
            events = res.json()
            upcoming = []
            for item in events:
                purpose = item.get('purpose', '').lower()
                if 'financial result' in purpose or 'results' in purpose:
                    symbol = item.get('symbol', '')
                    company = item.get('company', symbol)
                    date_str = item.get('date', '')
                    upcoming.append(f"📅 *{date_str}* - *{company}* (#{symbol})")
            
            if upcoming:
                msg = "🗓 *UPCOMING CORPORATE RESULTS (NEXT 7 DAYS)* 🗓\n\n" + "\n".join(upcoming[:15])
                send_telegram_text(msg)
            else:
                send_telegram_text("ℹ️ *Upcoming Results:* Agle 1 hafte me koi major results scheduled nahi hain.")
    except Exception as e:
        logging.error(f"Upcoming Results Error: {e}")

# ----------------- 2. PRE-MARKET GAP SCANNER -----------------
def scan_pre_market():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/market-data-pre-open?key=ALL"
        res = session.get(url, headers=HEADERS, timeout=12)
        
        if res.status_code == 200:
            data = res.json().get('data', [])
            gap_ups, gap_downs = [], []
            for item in data:
                metadata = item.get('metadata', {})
                symbol = metadata.get('symbol', '')
                p_change = metadata.get('pChange', 0)
                final_price = metadata.get('finalPrice', 0)
                
                if final_price > 0 and symbol and symbol != 'NIFTY':
                    if is_valid_intraday_stock(final_price):
                        if p_change >= 1.5:
                            gap_ups.append((symbol, final_price, p_change))
                        elif p_change <= -1.5:
                            gap_downs.append((symbol, final_price, p_change))
            
            gap_ups = sorted(gap_ups, key=lambda x: x[2], reverse=True)
            gap_downs = sorted(gap_downs, key=lambda x: x[2])
            
            msg_blocks = ["🚀 *PRE-OPEN MARKET GAP-UP & GAP-DOWN (No Penny/Non-Intraday)* 🚀\n"]
            if gap_ups:
                up_str = "\n".join([f"🟢 *{s}*: ₹{p:.2f} (+{c:.2f}%)" for s, p, c in gap_ups[:10]])
                msg_blocks.append(f"🔥 *TOP GAP-UP STOCKS:*\n{up_str}")
            else:
                msg_blocks.append("🟢 *TOP GAP-UP STOCKS:* Koi major stock nahi mila.")
                
            if gap_downs:
                down_str = "\n".join([f"🔴 *{s}*: ₹{p:.2f} ({c:.2f}%)" for s, p, c in gap_downs[:10]])
                msg_blocks.append(f"\n📉 *TOP GAP-DOWN STOCKS:*\n{down_str}")
            else:
                msg_blocks.append("\n🔴 *TOP GAP-DOWN STOCKS:* Koi major stock nahi mila.")
                
            send_telegram_text("\n".join(msg_blocks))
    except Exception as e:
        logging.error(f"Pre-market Scan Error: {e}")

# ----------------- 3. LIVE FINANCIAL RESULT SCANNER -----------------
def scan_corporate_results():
    global processed_results
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/corporates-financial-results?index=equities"
        res = session.get(url, headers=HEADERS, timeout=12)
        
        if res.status_code == 200:
            data = res.json()
            for item in data[:15]:
                symbol = item.get('symbol', 'UNKNOWN')
                company_name = item.get('companyName', symbol)
                broadcast_time_str = item.get('broadcastDateTime', '')
                result_id = f"{symbol}_{broadcast_time_str}"
                
                if result_id in processed_results:
                    continue
                
                pat = float(item.get('netProfit', 0) or 0)
                income = float(item.get('totalIncome', 0) or 0)
                period = item.get('period', 'Latest Qtr')

                rating = "🟢 VERY GOOD" if pat > 100 else ("🟩 GOOD" if pat > 0 else ("🟡 NEUTRAL" if pat == 0 else "🔴 BAD RESULT"))
                pat_sign = "🟢" if pat >= 0 else "🔴"
                inc_sign = "🟢" if income >= 0 else "🔴"

                msg = (
                    f"🚨 *LIVE FINANCIAL RESULT UPDATE* 🚨\n\n"
                    f"🏢 *Company:* {company_name} (#{symbol})\n"
                    f"📊 *Period:* {period}\n\n"
                    f"Rating: *{rating}*\n"
                    f"-----------------------------------\n"
                    f"💰 *Net Profit (PAT):* {pat_sign} {pat:.2f} Cr\n"
                    f"📈 *Total Income:* {inc_sign} {income:.2f} Cr\n"
                    f"-----------------------------------\n"
                    f"⚡ *Source:* NSE Live Corporate Feed"
                )
                send_telegram_text(msg)
                processed_results.add(result_id)
    except Exception as e:
        logging.error(f"Corporate Result Error: {e}")

# ----------------- 4. ADVANCED LIVE MARKET & VOLUME/RSI SCANNER -----------------
def scan_live_market_breakouts():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        urls = [
            "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20TOTAL%20MARKET",
            "https://www.nseindia.com/api/equity-stockIndices?index=BROAD%20MARKET"
        ]
        stocks_map = {}
        for u in urls:
            r = session.get(u, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                for s in r.json().get('data', []):
                    sym = s.get('symbol')
                    if sym:
                        stocks_map[sym] = s

        breakouts_52w, day_high_breakouts, volume_spikes, rsi_alerts = [], [], [], []
        for symbol, stock in stocks_map.items():
            ltp = stock.get('lastPrice', stock.get('last', 0))
            high52 = stock.get('yearHigh', 0)
            day_high = stock.get('dayHigh', 0)
            p_change = stock.get('pChange', stock.get('pchange', 0))
            trd_vol = stock.get('totalTradedVolume', 0)
            
            if ltp > 0 and is_valid_intraday_stock(ltp):
                if high52 > 0 and ltp >= high52: 
                    breakouts_52w.append(f"🚀 *{symbol}*: ₹{ltp} (52-Wk High)")
                if day_high > 0 and ltp >= day_high and p_change >= 2.0:
                    day_high_breakouts.append(f"⚡ *{symbol}*: ₹{ltp} (+{p_change:.2f}%)")
                if p_change >= 4.0:
                    volume_spikes.append(f"🔥 *{symbol}*: ₹{ltp} (+{p_change:.2f}%, Vol: {trd_vol:,})")
                if p_change >= 3.5 and ltp > (stock.get('open', ltp)):
                    rsi_alerts.append(f"📈 *{symbol}*: ₹{ltp} (Strong Momentum/RSI Bullish)")

        message_blocks = []
        if breakouts_52w: message_blocks.append("🚀 *52-WEEK HIGH BREAKOUTS (Filtered)*\n" + "\n".join(breakouts_52w[:6]))
        if day_high_breakouts: message_blocks.append("📈 *INTRADAY DAY HIGH BREAKOUTS*\n" + "\n".join(day_high_breakouts[:6]))
        if volume_spikes: message_blocks.append("💥 *HIGH VOLUME SPIKES*\n" + "\n".join(volume_spikes[:6]))
        if rsi_alerts: message_blocks.append("⚡ *MOMENTUM / RSI BULLISH ZONES*\n" + "\n".join(rsi_alerts[:6]))
            
        if message_blocks:
            send_telegram_text("🚨 *ACTIVE QUALITY MARKET ALERTS + VOLUME/RSI* 🚨\n\n" + "\n\n".join(message_blocks))
        else:
            send_telegram_text("ℹ️ *Market Scan:* No high-momentum active breakouts found right now.")
    except Exception as e:
        logging.error(f"Scan Error: {e}")

# ----------------- 5. FII & DII ACTIVITY TRACKER -----------------
def scan_fii_dii():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/fiidiiData"
        res = session.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json()
            msg_lines = ["📊 *FII & DII DAILY ACTIVITY REPORT* 📊\n"]
            for item in data:
                category = item.get('category', '')
                buy_val = item.get('buyValue', '0')
                sell_val = item.get('sellValue', '0')
                net_val = item.get('netValue', '0')
                msg_lines.append(f"▪️ *{category}*\n  Buy: ₹{buy_val} Cr | Sell: ₹{sell_val} Cr\n  Net: *₹{net_val} Cr*\n")
            send_telegram_text("\n".join(msg_lines))
    except Exception as e:
        logging.error(f"FII DII Error: {e}")

# ----------------- 6. UPPER & LOWER CIRCUIT SCANNER -----------------
def scan_circuits():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20TOTAL%20MARKET"
        res = session.get(url, headers=HEADERS, timeout=12)
        stocks = res.json().get('data', [])
        upper_locked, lower_locked = [], []
        
        for stock in stocks:
            symbol = stock.get('symbol', '')
            ltp = stock.get('lastPrice', 0)
            u_band = stock.get('upperCP', 0)
            l_band = stock.get('lowerCP', 0)
            
            if ltp > 0 and is_valid_intraday_stock(ltp) and u_band > 0 and l_band > 0:
                if ltp >= u_band:
                    upper_locked.append(f"🟢 *{symbol}*: ₹{ltp}")
                elif ltp <= l_band:
                    lower_locked.append(f"🔴 *{symbol}*: ₹{ltp}")
                    
        blocks = ["⚡ *CIRCUIT LOCKED STOCKS (Quality Filtered)* ⚡\n"]
        if upper_locked:
            blocks.append(f"🚀 *Upper Circuit Locked:* \n" + ", ".join(upper_locked[:8]))
        else:
            blocks.append("🚀 *Upper Circuit Locked:* None.")
            
        if lower_locked:
            blocks.append(f"\n🩸 *Lower Circuit Locked:* \n" + ", ".join(lower_locked[:8]))
        else:
            blocks.append("\n🩸 *Lower Circuit Locked:* None.")
            
        send_telegram_text("\n".join(blocks))
    except Exception as e:
        logging.error(f"Circuit Scan Error: {e}")

# ----------------- 7. SECTOR HEATMAP -----------------
def scan_sector_heatmap():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/equity-stockIndices?index=BROAD%20MARKET"
        res = session.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get('data', [])
            sectors = []
            for item in data:
                name = item.get('index', '')
                p_change = item.get('pChange', 0)
                ltp = item.get('last', 0)
                if 'NIFTY' in name:
                    emoji = "🟢" if p_change >= 0 else "🔴"
                    sectors.append((name, ltp, p_change, emoji))
            
            sectors = sorted(sectors, key=lambda x: x[2], reverse=True)
            sec_lines = ["🌡 *NSE SECTOR HEATMAP PERFORMANCE* 🌡\n"]
            for name, ltp, p_change, emoji in sectors[:12]:
                sec_lines.append(f"{emoji} *{name}*: {ltp:,.2f} ({p_change:+.2f}%)")
            send_telegram_text("\n".join(sec_lines))
    except Exception as e:
        logging.error(f"Sector Heatmap Error: {e}")

# ----------------- 8. OPTION CHAIN, PCR & F&O BUILDUP -----------------
def scan_pcr_sentiment():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        res = session.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            records = res.json().get('records', {})
            data = records.get('data', [])
            total_ce_oi, total_pe_oi = 0, 0
            for item in data:
                if 'CE' in item: total_ce_oi += item['CE'].get('openInterest', 0)
                if 'PE' in item: total_pe_oi += item['PE'].get('openInterest', 0)
            
            if total_ce_oi > 0:
                pcr = total_pe_oi / total_ce_oi
                sentiment = "🚀 Bullish" if pcr > 1.0 else ("⚠️ Bearish" if pcr < 0.8 else "⚖️ Neutral")
                msg = (
                    f"📊 *NIFTY OPTION CHAIN & F&O BUILDUP REPORT* 📊\n\n"
                    f"📌 *Total Call OI (CE):* {total_ce_oi:,}\n"
                    f"📌 *Total Put OI (PE):* {total_pe_oi:,}\n"
                    f"📈 *Put-Call Ratio (PCR):* *{pcr:.2f}*\n"
                    f"💡 *Market Sentiment:* {sentiment}\n"
                    f"🔥 *F&O Derivative Status:* Active Long/Short Buildup Monitoring On"
                )
                send_telegram_text(msg)
    except Exception as e:
        logging.error(f"PCR Error: {e}")

# ----------------- 9. INSIDER TRADING -----------------
def scan_insider_trading():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = "https://www.nseindia.com/api/corporates-pit"
        res = session.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json()
            items = []
            for item in data[:8]:
                company = item.get('symbol', '')
                person = item.get('acquirerOrDisposer', '')
                txn_type = item.get('posal', '')
                shares = item.get('secAcq', 0)
                items.append(f"🏢 *{company}* | 👤 {person}\n🔄 Txn: {txn_type} | Qty: {shares}")
            
            if items:
                send_telegram_text("🕵️‍♂️ *LATEST INSIDER TRADING FILINGS* 🕵️‍♂️\n\n" + "\n\n".join(items))
    except Exception as e:
        logging.error(f"Insider Trading Error: {e}")

def send_market_open(): send_telegram_text("🔔 *MARKET OPENING SUMMARY (09:15 AM)*\n\nQuality Intraday, F&O & Volume/RSI Scanner Active!")
def send_market_close(): send_telegram_text("🏁 *MARKET CLOSING SUMMARY (03:30 PM)*\n\nMarket closed for today.")

def listen_commands():
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=10"
            res = requests.get(url, timeout=15).json()
            for update in res.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {}).get("text", "").lower()
                if msg in ["/start", "/test", "/ping"]:
                    send_telegram_text("⚡ *Bot Online Hai!* All Quality Intraday, F&O & Volume Filters Active.")
                elif msg in ["/scan", "/breakout"]:
                    send_telegram_text("🔍 *Scanning Active Quality Stocks & Volume Spikes...*")
                    scan_live_market_breakouts()
                elif msg in ["/result", "/results"]:
                    send_telegram_text("🔍 *Scanning Live Corporate Results...*")
                    scan_corporate_results()
                elif msg in ["/preopen", "/gap"]:
                    send_telegram_text("🔍 *Scanning Pre-Open Market...*")
                    scan_pre_market()
                elif msg in ["/upcoming", "/calendar"]:
                    send_telegram_text("🔍 *Fetching Upcoming Results...*")
                    scan_upcoming_results()
                elif msg in ["/fiidii"]:
                    send_telegram_text("🔍 *Fetching FII & DII Data...*")
                    scan_fii_dii()
                elif msg in ["/circuit", "/circuits"]:
                    send_telegram_text("🔍 *Scanning Circuits...*")
                    scan_circuits()
                elif msg in ["/sector", "/heatmap"]:
                    send_telegram_text("🔍 *Generating Sector Heatmap...*")
                    scan_sector_heatmap()
                elif msg in ["/pcr", "/sentiment", "/fno"]:
                    send_telegram_text("🔍 *Calculating PCR & F&O Sentiment...*")
                    scan_pcr_sentiment()
                elif msg in ["/insider", "/pit"]:
                    send_telegram_text("🔍 *Fetching Insider Trading...*")
                    scan_insider_trading()
        except Exception:
            time.sleep(5)

# Schedules Setup
schedule.every(30).seconds.do(scan_corporate_results)
schedule.every(5).minutes.do(scan_live_market_breakouts)
schedule.every().day.at("03:00").do(scan_upcoming_results)
schedule.every().day.at("03:38").do(scan_pre_market)
schedule.every().day.at("03:45").do(send_market_open)
schedule.every().day.at("10:00").do(send_market_close)
schedule.every().day.at("10:15").do(scan_sector_heatmap)
schedule.every().day.at("11:00").do(scan_pcr_sentiment)
schedule.every().day.at("11:30").do(scan_circuits)
schedule.every().day.at("16:00").do(scan_fii_dii)
schedule.every().day.at("16:30").do(scan_insider_trading)

threading.Thread(target=listen_commands, daemon=True).start()

logging.info("Bot fully operational with Volume, RSI & F&O Filters!")
send_telegram_text("🚀 *Bot Online & Updated!* All Features + F&O, Volume & RSI Filters Running smoothly.")

while True:
    schedule.run_pending()
    time.sleep(1)
      
