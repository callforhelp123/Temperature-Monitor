import pickle
import requests
import smtplib 
from os import path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from time import sleep
from datetime import datetime
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 
from password import returnPassword, returnOWMAPIkey


class Sheets_Logging:
    """ this class holds the authorization service for the spreadsheet
        it also has all the functions necessary for interacting w/ Sheets API
    """
    SPREADSHEET_ID = '121BrpHHTBJlJzvaev-grbtioXInxn9LMmwMZwZadjQM'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']

    def __init__(self):
        self.service = None
        self.auth()
        self.current_date = "Sheet1"

    def auth(self):
        """authorization service"""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('sheets', 'v4', credentials=creds)

    def write_data(self, data):
        """ writes temperature data to a sheet, named the current date"""
        service = self.service
        values = [data]
        body = {
            'values': values
        }
        curr_time = datetime.now()
        curr_date = str(curr_time.year) + "/" + str(curr_time.month) + "/" + str(curr_time.day)
        # new date means we need to create a new sheet + chart
        if self.current_date != curr_date:
            self.current_date = curr_date
            try:
                self.create_new_sheet(service, self.current_date)
                self.create_chart(service, self.current_date)
            except:
                print('sheet already exists')
        # write the information to the sheet w/ current date
        range_name = self.current_date
        result = service.spreadsheets().values().append(
            spreadsheetId=self.SPREADSHEET_ID, range=range_name,
            valueInputOption='USER_ENTERED', body=body).execute()
        print(values)

    def create_new_sheet(self, service, sheet_name):
        """ creates a new sheet at index 0. maintains a history of 31 days."""
        sheet_metadata = service.spreadsheets().get(spreadsheetId=self.SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])

        # maintain a history of 31 days
        if len(sheets) > 31:
            for sheet in sheets:
                sheetID = sheet['properties']['sheetId']
            delete_request = {
                "requests": [
                    {
                  "deleteSheet": {
                    "sheetId": sheetID
                        }
                    }
                ]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=self.SPREADSHEET_ID,
                body=delete_request
            ).execute()

        # create a new sheet at index 0 with current date
        batch_update_spreadsheet_request = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "index": 0
                        }
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID,
            body=batch_update_spreadsheet_request
        ).execute()

    def create_chart(self, service, sheet_name):       
        """ creates a line chart for the new sheet"""
        # Get the sheetId for the new sheet; dunno if can create chart in sheet by title, so using ID
        sheet_metadata = service.spreadsheets().get(spreadsheetId=self.SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])
        sheet_id = None
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                sheet_id = sheet['properties']['sheetId']
                break

        # Define the chart specification
        chart_spec = {
            "title": "Temperature Chart",
            "basicChart": {
                "chartType": "LINE",
                "domains": [
                    {
                        "domain": {
                            "sourceRange": {
                                "sources": [
                                    {
                                        "sheetId": sheet_id,
                                        "startRowIndex": 0,
                                        "endRowIndex": 2000,
                                        "startColumnIndex": 0,
                                        "endColumnIndex": 1,
                                    }
                                ]
                            }
                        }
                    }
                ],
                "series": [
                    {
                        "series": {
                            "sourceRange": {
                                "sources": [
                                    {
                                        "sheetId": sheet_id,
                                        "startRowIndex": 0,
                                        "endRowIndex": 2000,
                                        "startColumnIndex": 1,
                                        "endColumnIndex": 2,
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }

        requests = [
            {
                "addChart": {
                    "chart": {
                        "spec": chart_spec,
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheet_id,
                                    "rowIndex": 3,
                                    "columnIndex": 5
                                }
                            },
                        }
                    },
                }
            }
        ]

        # Execute the batchUpdate request to create the chart
        service.spreadsheets().batchUpdate(spreadsheetId=self.SPREADSHEET_ID, body={"requests": requests}).execute()


class Temp_Controls:

    def __init__(self):
        # user controlled variables here
        self.boundary_temp = 52  # will be in celsius, currently F
        self.emails = ["snowsoftj4c@gmail.com"]  # separate by comma
        self.notification_cooldown = 3600  # in seconds

        # program variables, no touchy
        self.notify = False
        self.notify_timer = 0
        self.time_under = ""

    def measure_temp(self):
        """ measures temperature from raspberry Pi """
        owm_api_key = returnOWMAPIkey()
        weather = requests.get(
            f"https://api.openweathermap.org/data/2.5/onecall?lat={47.6}&lon={-122.3}&exclude=minutely&appid={owm_api_key}&units=imperial")
        weather = weather.json()
        temp = weather["current"]["temp"]
        return temp

    def gen_data(self):
        temp = self.measure_temp()
        date = datetime.now()
        return [str(date).split('.')[0], temp]

    def send_all_clear_mail(self):
        # initialize connection to gmail server
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        password = returnPassword()
        # credentials + email destinations goes here
        smtp.login('tempsensor486@gmail.com', password)
        to = self.emails
        # construct message
        msg = MIMEMultipart() 
        msg['Subject'] = f"Good news; temperature is now below {self.boundary_temp}"
        msg_body = f"Spent from {temp_controller.time_under} to {str(datetime.now()).split('.')[0]} out of range"
        msg.attach(MIMEText(msg_body))   
        smtp.sendmail(from_addr="hello@gmail.com", to_addrs=to, msg=msg.as_string())
        smtp.quit()

    def send_warning_mail(self, curr_temp):
        # initialize connection to gmail server
        smtp = smtplib.SMTP('smtp.gmail.com', 587) 
        smtp.ehlo() 
        smtp.starttls() 
        password = returnPassword()
        # credentials + email destinations goes here 
        smtp.login('tempsensor486@gmail.com', password) 
        to = self.emails
        # construct message
        msg = MIMEMultipart() 
        msg['Subject'] = f"Warning: Temperature at {curr_temp}F"
        msg_body = f"Temperature has been above {self.boundary_temp}F since {self.time_under}"
        msg.attach(MIMEText(msg_body))   
        smtp.sendmail(from_addr="hello@gmail.com", 
                    to_addrs=to, msg=msg.as_string()) 
        smtp.quit()


if __name__ == '__main__':
    gsheet = Sheets_Logging()
    temp_controller = Temp_Controls()
    loop = True
    while loop:
        # retrieve temperature info
        try:
            data = temp_controller.gen_data()
        except:
            print('error in weather retrieval')

        # write to google sheet
        try:
            gsheet.write_data(data=data)
        except:
            print('error in google write')

        # email notification if temp is past boundary temp
        if data[1] > temp_controller.boundary_temp:
            if not temp_controller.notify:
                temp_controller.notify = True
                temp_controller.time_under = str(datetime.now()).split('.')[0]
        else:
            # if temp has successfully recovered
            if temp_controller.notify:
                temp_controller.send_all_clear_mail()
                print("all clear notification sent")
            temp_controller.notify = False
            temp_controller.notify_timer = 0

        # send notification every hour
        if temp_controller.notify:
            if temp_controller.notify_timer >= temp_controller.notification_cooldown:
                temp_controller.notify_timer = 0
            if temp_controller.notify_timer == 0:
                temp_controller.send_warning_mail(str(data[1]))
                print("warning notification sent")
            temp_controller.notify_timer += 120
        print("interval_timer: ", temp_controller.notify_timer)
        sleep(120)