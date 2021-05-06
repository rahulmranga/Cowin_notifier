
import pandas as pd
import requests
import numpy as np
import datetime
import numpy as np
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
            url="https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}".format(state_code)
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            response = requests.get(url,headers=headers)
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
    df_pincode=pd.DataFrame(columns=['center','date','capacity','pincode'])
    pin_code_available=False
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={}&date={}".format(pincode, today)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(URL,headers=headers)
    if response.ok:
        centers_pincode=json.loads(response.text)
        pin_code_available=True
        for i in centers_pincode['centers']:
            for j in i['sessions']: 
                if(j['min_age_limit']<=age):
                    df_pincode=df_pincode.append({'center':i['name'],'date':j['date'],'capacity':j['available_capacity'],'pincode':i['pincode']},ignore_index=True)             
            #if df_pincode.capacity.sum()==0:
                #df_pincode=pd.DataFrame(columns=['center','date','capacity','pincode'])
                #pin_code_available=False
    return pin_code_available,df_pincode
   


def district_availability(dist_id,age):
    df_dist=pd.DataFrame(columns=['center','date','capacity','pincode'])
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(dist_id,today)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(URL,headers=headers)
    dist_available=False
    if response.ok:
        centers_dist=json.loads(response.text)
        dist_available=True
        for i in centers_dist['centers']:
            for j in i['sessions']: 
                if(j['min_age_limit']<=age):
                    df_dist=df_dist.append({'center':i['name'],'date':j['date'],'capacity':j['available_capacity'],'pincode':i['pincode']},ignore_index=True)             
                if df_dist.capacity.sum()==0:
                    df_dist=pd.DataFrame(columns=['center','date','capacity','pincode'])
                    dist_available=False
    return dist_available,df_dist
    
def send_email_available(df,email,name,level):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "Vaccination Centers available"
        msg['From'] = 'cowinvaccinedev@gmail.com'
        name=name
        df=df[df['capacity']>0]
        receiver_email = email
        
        df=df.pivot(index=['center','pincode'],columns='date',values='capacity').replace(np.nan,0)
        html = """\
        <html>
          <head></head>
          <body>
          Hi {0},<br>
          These are the centers available in your {1}. Please book an appointment in COWIN portal: https://www.cowin.gov.in/ <br>
            {2}<br>
            Stay Safe! <br>
            <br>
            To unsubcribe to updates please respond to this mail
          </body>
        </html>
        """.format(name,level,df.to_html())
        
        part1 = MIMEText(html, 'html')
        msg.attach(part1)
        
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print('vaccination available sent to {} at {}'.format(receiver_email,datetime.datetime.now()))
            
    except:
        msg = MIMEMultipart()
        msg['Subject'] = "Vaccination Centers available"
        msg['From'] = 'cowin.vaccine.alerts@gmail.com'
        name=name
        receiver_email = email
        df=df[df['capacity']>0]
        
        df=df.pivot(index=['center','pincode'],columns='date',values='capacity').replace(np.nan,0)
        html = """\
        <html>
          <head></head>
          <body>
          Hi {0},<br>
          These are the centers available in your {1}. Please book an appointment in COWIN portal: https://www.cowin.gov.in/ <br>
            {2}<br>
            Stay Safe! <br>
            <br>
            To unsubscribe to updates please respond to this mail
          </body>
        </html>
        """.format(name,level,df.to_html())
        
        part1 = MIMEText(html, 'html')
        msg.attach(part1)
        
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email2, password)
            server.sendmail(sender_email2, receiver_email, msg.as_string())
            print('vaccination available sent to {} at {}'.format(receiver_email,datetime.datetime.now()))
    
        
def email_not_available(email_ids):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "Vaccination not available for age group"
        msg['From'] = 'cowinvaccinedev@gmail.com'
        
        receiver_email=email_ids
        
        html = """\
            <html>
              <head></head>
              <body>
              Hi,<br>
              Vaccination is not available for your age group in your district.
              <br> Due to email limits enforced by gmail and to limit spamming of your inbox, you will be getting an email ONLY if a vaccination center is available near you
              Stay Safe!
              <br> For real time updates visit the link here: https://bettercowin.org/
              <br> To unsubscribe to updates please respond to this mail 
              <br>
              
              
              </body>
            </html>
            """
            
        part1 = MIMEText(html, 'html')
        msg.attach(part1)
                        
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print('vaccination not available sent to {} at {}'.format(receiver_email,datetime.datetime.now()))
            
    except:
        msg = MIMEMultipart()
        msg['Subject'] = "Vaccination not available for age group"
        msg['From'] = 'cowin.vaccine.alerts@gmail.com'
          
        receiver_email=email_ids
        
        html = """\
            <html>
              <head></head>
              <body>
              Hi,<br>
              Vaccination is not available for your age group in your district. <br>
              <br> Due to email limits enforced by gmail and to limit spamming of your inbox, you will be getting an email ONLY if a vaccination center is available near you
              Stay Safe!
              <br> For real time updates visit the link here: https://bettercowin.org/
              <br> To unsubscribe to updates please respond to this mail 
              <br>
              
              
              </body>
            </html>
            """
            
        part1 = MIMEText(html, 'html')
        msg.attach(part1)
            
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email2, password)
            server.sendmail(sender_email2, receiver_email, msg.as_string())
            print('vaccination not available sent to {} ppl at {}'.format(len(receiver_email),datetime.datetime.now()))
        
        
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
port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "cowinvaccinedev@gmail.com"  # Enter your address
sender_email2="cowin.vaccine.alerts@gmail.com"
#receiver_email = email  # Enter receiver address
password = ""
context = ssl.create_default_context()

df['not_available']=np.nan
df=df[df['Age']<=45]

for i in range(0,len(df)):
    try:
        pincode=df.iloc[i,3]
        age=df.iloc[i,4]
        pin_code_available,df_pin=pincode_availability(pincode, age)
        
        if (len(df_pin)==0) or (df_pin.capacity.sum()==0):
            age_availability_1=False 
        else:
            age_availability_1=True
        
        if age_availability_1 is False:
            df_districts=get_district_code()
            district_name=get_district_name(pincode)
            df_districts['string_match_dist']=[distance.get_jaro_distance(x, district_name) for x in df_districts['district_name']]
            dist_id=df_districts.loc[df_districts['string_match_dist'].idxmax()]['district_id']
            district_available,df_dist=district_availability(dist_id,age)
            if len(df_dist)==0:
                age_availability_2=False 
            else:age_availability_2=True
        
        count=count+1
        email=df.iloc[i,2]
        name=df.iloc[i,1]
        if (age_availability_1==True and df_pin.capacity.sum()>1):
            send_email_available(df_pin,email,name,'pincode')
            df.iloc[i,6]=df.iloc[i,6]+1
        elif age_availability_2==True and age_availability_1==False:
            if(df_dist.capacity.sum()==0): 
                df.iloc[i,6]=1
                #email_not_available(df.iloc[i,2],df.iloc[i,1])
            elif(df_dist.capacity.max()>1):
                send_email_available(df_dist,email,name,'district')
        else:
            df.iloc[i,6]=1
            #email_not_available(df.iloc[i,2],df.iloc[i,1])
    except Exception as e:
        print("error in line {} due to {}".format(i,e))
        if(e=='cannot unpack non-iterable NoneType object'):
            import time
            time.sleep(10)
        continue


f=open('log_cowin.txt','a')
f.write("Script ran successfully and sent emails to {0} ppl at {1} on {2}\n".format(count,datetime.datetime.now().strftime("%H:%M"),today))
f.close()
