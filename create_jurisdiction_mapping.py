import json

from utils.utils import fetch_api_response

state_url = 'https://cdn-api.co-vin.in/api/v2/admin/location/states'

district_url = 'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}'


def create_jurisdiction_mapping():
    """
    method to create state -> district mapping and save it to json file
    :return:
    """
    try:
        state_response = fetch_api_response(state_url)
        states = state_response.get('states', [])
        for state in states:
            state_specific_url = district_url.format(state.get('state_id', 0))
            district_response = fetch_api_response(state_specific_url)
            districts = district_response.get('districts', [])
            state['districts'] = districts
        with open("state-district.json", "w") as output_json_file:
            json.dump(states, output_json_file)
    except Exception as e:
        print(e)
