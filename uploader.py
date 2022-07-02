

from os import path
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

def upload(filename):
    SCOPES = ['https://www.googleapis.com/auth/drive']

    creds = None

    if path.exists('secrets/upload_token.json'):
        creds = Credentials.from_authorized_user_file('secrets/upload_token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'secrets/google_project_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('secrets/upload_token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
            'parents': ['1zG1e6zjWyvDVVj_0H54P9EiTuEZpiwPX'],
            'mimeType': 'application/vnd.google-apps.spreadsheet'
            }

        media = MediaFileUpload(filename, mimetype='application/xlsx')
        file = service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        print('File ID: {0}'.format(file.get('id')))

    except HttpError as error:
        print(f'An error occurred: {error}')
