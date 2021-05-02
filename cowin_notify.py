# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import requests
import datetime
import json
from pyjarowinkler import distance
import smtplib
import ssl
import gspread
from oauth2client.service_account import ServiceAccountCredentials 
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


####Gets the district code for each district in the country######

def get_district_code():
    df_districts=pd.DataFrame([{'district_id':-1,'district_name':'unknown'}])
    for state_code in range(0,50):
        try:
            response = requests.get("https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}".format(state_code))
            json_data = json.loads(response.text)
            for i in json_data["districts"]:
                df_districts=df_districts.append(i,ignore_index=True)
        except:
            break
    return df_districts


def get_district_name(pincode):
    response=requests.get("http://postalpincode.in/api/pincode/{}".format(pincode))
    json_state=json.loads(response.text)
    
    return(json_state['PostOffice'][0]['District'])


#####Check in centers in pincode################

def pincode_availability(pincode,age):
    df_pincode=pd.DataFrame(columns=['center','date','capacity'])
    pin_code_available=False
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={}&date={}".format(pincode, today)
    response = requests.get(URL)
    if response.ok:
        centers_pincode=json.loads(response.text)
        pin_code_available=True
        for i in centers_pincode['centers']:
            for j in i['sessions']: 
                if(j['min_age_limit']<=age):
                    df_pincode=df_pincode.append({'center':i['name'],'date':j['date'],'capacity':j['available_capacity']},ignore_index=True)             
        return pin_code_available,df_pincode





def district_availability(dist_id,age):
    df_dist=pd.DataFrame(columns=['center','date','capacity','city/town'])
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(dist_id,today)
    response = requests.get(URL)
    dist_available=False
    if response.ok:
        centers_dist=json.loads(response.text)
        dist_available=True
        for i in centers_dist['centers']:
            for j in i['sessions']: 
                if(j['min_age_limit']<=age):
                    df_dist=df_dist.append({'center':i['name'],'date':j['date'],'capacity':j['available_capacity']},ignore_index=True)             
        return dist_available,df_dist

def send_email_available(df,email,name,level):
        
   
    msg = MIMEMultipart()
    msg['Subject'] = "Vaccination Centers available"
    msg['From'] = 'cowinvaccinedev@gmail.com'
    name=name
    
    html = """\
    <html>
      <head></head>
      <body>
      Hi {0},<br>
      These are the centers available in your {1}. Please book an appointment in COWIN portal <br>
        {2}<br>
        Stay Safe!
      </body>
    </html>
    """.format(name,level,df.to_html())
    
    part1 = MIMEText(html, 'html')
    msg.attach(part1)
    
    
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "cowinvaccinedev@gmail.com"  # Enter your address
    receiver_email = email  # Enter receiver address
    password = "cowin@2021"
    context = ssl.create_default_context()

    
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def email_not_available(email,name):
    msg = MIMEMultipart()
    msg['Subject'] = "Vaccination not available for age group"
    msg['From'] = 'cowinvaccinedev@gmail.com'
    name=name
    
    html = """\
    <html>
      <head></head>
      <body>
      Hi {0},<br>
      Vaccination is not available for your age group in your district. <br>
      Stay Safe!
      </body>
    </html>
    """.format(name)
    
    part1 = MIMEText(html, 'html')
    msg.attach(part1)
    
    
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "cowinvaccinedev@gmail.com"  # Enter your address
    receiver_email = email  # Enter receiver address
    password = "cowin@2021"
    context = ssl.create_default_context()
    
        
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

        
        
today=datetime.datetime.today().strftime("%d-%m-%y")


# define the scope
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# load credentials from env, form json and pass it to google API to validate your credentials
json_key = json.load(open("creds.json"))

credentials=json_key

api_credential = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)

# authorize the clientsheet
client = gspread.authorize(api_credential)


workbook = client.open('CoWIN Portal Notification (Responses)')
# Get the first sheet
sheet = workbook.sheet1
df = pd.DataFrame(sheet.get_all_records())
count=0

for i in range(0,len(df)):
    try:
        pin_code_available,df_pin=pincode_availability(df.iloc[i,3], df.iloc[i,4])
        
        if len(df_pin)==0:
            age_availability_1=False 
        else:age_availability_1=True
        
        if age_availability_1 is False:
            df_districts=get_district_code()
            district_name=get_district_name(df.iloc[i,3])
            df_districts['string_match_dist']=[distance.get_jaro_distance(x, district_name) for x in df_districts['district_name']]
            dist_id=df_districts.loc[df_districts['string_match_dist'].idxmax()]['district_id']
            district_available,df_dist=district_availability(dist_id,df.iloc[i,4])
            if len(df_dist)==0:
                age_availability_2=False 
            else:age_availability_2=True
        
        count=count+1
        if age_availability_1==True:
            send_email_available(df_pin,df.iloc[i,2],df.iloc[i,1],'pincode')
        elif age_availability_2==True and age_availability_1==False:
            if(df_dist.capacity.sum()==0): 
                email_not_available(df.iloc[i,2],df.iloc[i,1])
            else:
                send_email_available(df_dist,df.iloc[i,2],df.iloc[i,1],'district')
        else:
            email_not_available(df.iloc[i,2],df.iloc[i,1])
    except:
        continue
    


f=open('log_cowin.txt','w+')
f.write("Script ran successfully and sent emails to {0} ppl at {1} on {2}".format(count,datetime.datetime.now().strftime("%H:%M"),today))
