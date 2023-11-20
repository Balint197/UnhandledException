import json, requests

def get_conversion_rate_of_currencies(currency_1, currency_2):
    """Get the current conversion rate between two currencies"""
    currency_1 = currency_1.upper()
    currency_2 = currency_2.upper()
    api_key = "cur_live_O8lr4Uj4Nq0TeugOVUwxDg7ruGMhclEJtFTFsfGr"  # your https://currencyapi.com/docs/convert API key
    url = "https://api.currencyapi.com/v3/latest"
    headers = {
        "apikey": api_key,
        "value": "1",
        "base_currency": currency_1,
        "currencies": currency_2,
    }
    try:
        response = requests.request("GET", url, headers=headers)
        val = response.json()["data"][currency_2]["value"]
        weather_info = {
            "Currency 1": currency_1,
            "Currency 2": currency_2,
            "Conversion rate": str(val),
        }
    except Exception as e:
        print(e)
        currency_info = {
            "Currency 1": currency_1,
            "Currency 2": currency_2,
            "Conversion rate": "Unknown",
        }

    return json.dumps(currency_info)
