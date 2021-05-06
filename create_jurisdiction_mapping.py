import json

import requests

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko)'
                         ' Chrome/39.0.2171.95 Safari/537.36'}
state_url = 'https://cdn-api.co-vin.in/api/v2/admin/location/states'

district_url = 'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}'


def fetch_api_response(url, state_id=None):
    """
    generic method to fetch api response
    :param url:
    :param state_id:
    :return:
    """
    if state_id:
        url = url.format(state_id)

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    raise ValueError("API request failed")


def create_jurisdiction_mapping():
    """
    method to create state -> district mapping and save it to json file
    :return:
    """
    try:
        state_response = fetch_api_response(state_url)
        states = state_response.get('states', [])
        for state in states:
            district_response = fetch_api_response(district_url, state.get('state_id', 0))
            districts = district_response.get('districts', [])
            state['districts'] = districts
        with open("state-district.json", "w") as output_json_file:
            json.dump(states, output_json_file)
    except Exception as e:
        print(e)
