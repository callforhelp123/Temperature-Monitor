import pickle
import requests
from os import path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from time import sleep
from datetime import datetime

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

def measure_temp():
    """ measures temperature from raspberry Pi """
    owm_api_key = "###"
    weather = requests.get(
        f"https://api.openweathermap.org/data/2.5/onecall?lat={47.6}&lon={-122.3}&exclude=minutely&appid={owm_api_key}&units=imperial")
    weather = weather.json()
    temp = weather["current"]["temp"]
    return temp

def gen_data():
    temp = measure_temp()
    date = datetime.now()
    return [str(date).split('.')[0], temp]


if __name__ == '__main__':
    gsheet = Sheets_Logging()
    loop = True
    while loop:
        data = gen_data()
        # sometimes encounter a random network error, try/except work around
        try:
            gsheet.write_data(data=data)
        except:
            print('possible network error, trying again in 5 minutes to reduce cooldown')
            sleep(300)
        sleep(120)