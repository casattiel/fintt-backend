import requests

# Función para obtener precios de acciones
def get_stock_price(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "apikey": "TU_CLAVE_API"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["Time Series (5min)"] if "Time Series (5min)" in data else None

# Función para obtener precios de criptomonedas
def get_crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol,
        "vs_currencies": "usd"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get(symbol, {}).get("usd", None)
