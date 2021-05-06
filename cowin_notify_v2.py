import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# define the scope
from utils.utils import fetch_api_response

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# load credentials from env, form json and pass it to google API to validate your credentials
api_credential = ServiceAccountCredentials.from_json_keyfile_name('google_cred.json', scope)  # load your cred file

# authorize the clientsheet
client = gspread.authorize(api_credential)

# fetch it form env
sheet_link = 'sample.html'

vaccine_availability_url = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode={pin}&date={date}'


def fetch_sheet_data(g_sheet_link):
    """
    :param g_sheet_link
    method to fetch data from google sheet
    :return:
    """
    sheet = client.open_by_url(g_sheet_link)
    sheet_instance = sheet.get_worksheet(0)
    records_data = sheet_instance.get_all_records()
    return records_data


def fetch_vaccine_availability_by_pin(pin_code_session, age, pin_code):
    """
    method to fetch vaccine availability based on age and pin code
    :param pin_code:
    :param age:
    :param pin_code_session:
    :return:
    """
    sessions = pin_code_session.get(pin_code, [])
    availability_list = list()
    for session in sessions:
        session_min_age = session.get('min_age_limit', None)
        if session_min_age and age >= session_min_age:
            availability_dict = dict()
            availability_dict['name'] = session.get('name', '')
            availability_dict['address'] = session.get('address', '')
            availability_dict['pin_code'] = session.get('pincode', '')
            availability_dict['fee_type'] = session.get('fee_type', '')
            availability_dict['capacity'] = session.get('available_capacity', 0)
            availability_dict['vaccine'] = session.get('vaccine', 'NA')
            availability_dict['slots'] = session.get('slots', 'NA')
            availability_list.append(availability_dict)
    return availability_list


def create_vaccine_pin_code_dict(registered_pin_codes):
    """
    method to create vaccine pin code dictionary
    :param registered_pin_codes:
    :return:
    """
    date = datetime.today().strftime("%d-%m-%y")
    vaccine_session_dict = dict()
    for registered_pin_code in registered_pin_codes:
        pin_code_url = vaccine_availability_url.format(pin=registered_pin_code, date=date)
        api_response = fetch_api_response(pin_code_url)
        sessions = api_response.get('sessions', [])
        vaccine_session_dict[registered_pin_code] = sessions
    return vaccine_session_dict


def process_data():
    """
    fetch vaccine information for registered users
    :return:
    """
    users = fetch_sheet_data(sheet_link)
    registered_pin_codes = list(set([user.get('Pin') for user in users]))
    pin_code_session_dict = create_vaccine_pin_code_dict(registered_pin_codes)

    for user in users:
        name = user.get('Name', 'user')
        age = user.get('Age', None)
        email = user.get('Email', None)
        pin_code = user.get('Pin', None)
        if age and email and pin_code:
            vaccine_data = fetch_vaccine_availability_by_pin(pin_code_session_dict, age, pin_code)
            # send emails based on output of vaccine data -> form table else send not available email
