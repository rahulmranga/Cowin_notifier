import json

import requests

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko)'
                         ' Chrome/39.0.2171.95 Safari/537.36'}


def fetch_api_response(url):
    """
    generic method to fetch api response
    :param url:
    :return:
    """
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    raise ValueError("API request failed")
