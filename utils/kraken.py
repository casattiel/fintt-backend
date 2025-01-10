import os
import krakenex

kraken_api = krakenex.API()
kraken_api.key = os.getenv("KRAKEN_API_KEY")
kraken_api.secret = os.getenv("KRAKEN_SECRET_KEY")

def execute_trade(crypto_pair, amount, action):
    response = kraken_api.query_private('AddOrder', {
        'pair': crypto_pair,
        'type': action,
        'ordertype': 'market',
        'volume': amount
    })
    if response.get("error"):
        raise Exception(f"Kraken API error: {response['error']}")
    return response
