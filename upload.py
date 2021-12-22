



from os import write
from os import path
import numpy
import pandas as pd
import re
import json
import requests
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import configparser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None

if path.exists('upload_token.json'):
    creds = Credentials.from_authorized_user_file('upload_token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('upload_token.json', 'w') as token:
        token.write(creds.to_json())

try:
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': 'Ad_Split_October_2021.xlsx',
        'parents': ['1zG1e6zjWyvDVVj_0H54P9EiTuEZpiwPX'],
        'mimeType': 'application/vnd.google-apps.spreadsheet'
        }

    media = MediaFileUpload('output.xlsx', mimetype='application/xlsx')
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print('File ID: {0}'.format(file.get('id')))

except HttpError as error:
    print(f'An error occurred: {error}')
