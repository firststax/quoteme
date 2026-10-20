from flask import Flask, jsonify, send_from_directory
import yfinance as yf

app = Flask(__name__, static_folder='.')

# Server-seitige Watchlist
watchlist = []

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/stock/<ticker>')
def get_stock(ticker):
    try:
        t = ticker.upper()
        stock = yf.Ticker(t)
        
        # Aktueller Kurs
        data = stock.history(period="1d")
        if data.empty:
            return jsonify({"error": "Ticker nicht gefunden"}), 404
        latest_price = round(data['Close'].iloc[-1], 2)
        
        # Zusatzinfos (.info kann manchmal etwas dauern, liefert aber KGV & MarketCap)
        info = stock.info
        market_cap = info.get('marketCap')
        pe_ratio = info.get('trailingPE')
        
        # Market Cap formatieren (z.B. 1.52 bn oder 450.5 m)
        mc_str = "N/A"
        if market_cap:
            if market_cap >= 1e9:
                mc_str = f"{market_cap / 1e9:.2f}bn"
            else:
                mc_str = f"{market_cap / 1e6:.1f}m"
                
        # KGV formatieren
        pe_str = round(pe_ratio, 2) if pe_ratio else "N/A"

        return jsonify({
            "ticker": t,
            "price": latest_price,
            "marketCap": mc_str,
            "peRatio": pe_str
        })
    except Exception as e:
        print(f"Quote Fehler: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/watchlist/add/<ticker>')
def add_watchlist(ticker):
    t = ticker.upper()
    if t not in watchlist:
        watchlist.append(t)
    return jsonify({"watchlist": watchlist})

@app.route('/api/watchlist/remove/<ticker>')
def remove_watchlist(ticker):
    t = ticker.upper()
    if t in watchlist:
        watchlist.remove(t)
    return jsonify({"watchlist": watchlist})

@app.route('/api/watchlist/show')
def show_watchlist():
    results = []
    for t in watchlist:
        try:
            stock = yf.Ticker(t)
            data = stock.history(period="1d")
            if not data.empty:
                price = round(data['Close'].iloc[-1], 2)
                results.append({"ticker": t, "price": price})
            else:
                results.append({"ticker": t, "price": "N/A"})
        except Exception:
            results.append({"ticker": t, "price": "Fehler"})
    return jsonify({"watchlist": results})

import urllib.request
import xml.etree.ElementTree as ET

@app.route('/api/news/<ticker>')
def get_news(ticker):
    try:
        t = ticker.upper()
        url = f"https://news.google.com/rss/search?q={t}+stock&hl=en-US&gl=US&ceid=US:en"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        headlines = []
        
        for item in root.findall('.//item')[:5]:
            title_elem = item.find('title')
            source_elem = item.find('source')
            link_elem = item.find('link') # Link-Element auslesen
            
            title = title_elem.text if title_elem is not None else "Kein Titel"
            publisher = source_elem.text if source_elem is not None else "Google News"
            link = link_elem.text if link_elem is not None else "#"
            
            headlines.append({"title": title, "publisher": publisher, "link": link})
            
        return jsonify({"ticker": t, "news": headlines})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    print("Retro Terminal Server läuft auf http://127.0.0.1:5000")
    app.run(debug=True, port=5000)