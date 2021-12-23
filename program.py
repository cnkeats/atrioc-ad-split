



import uploader
import pandas as pd
import datetime
from os import path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/yt-analytics-monetary.readonly',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]
creds = None

if path.exists('download_token.json'):
    creds = Credentials.from_authorized_user_file('download_token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        #creds = flow.run_local_server(port=0)
        creds = flow.run_console()
    # Save the credentials for the next run
    with open('download_token.json', 'w') as token:
        token.write(creds.to_json())

playlistId = 'UUgv4dPk_qZNAbUW9WkuLPSA'

endpoint = 'https://www.googleapis.com/youtube/v3/playlistItems'
parts = [
    'snippet',
    #'contentDetails'
]

videos = []

pageToken = ''
morePages = True

while morePages:
    
    service = build('youtube', 'v3', credentials=creds)
    response = service.playlistItems().list(
        part=parts,
        playlistId=playlistId,
        maxResults=50,
        pageToken=pageToken
    ).execute()

    video = {}
    for item in response['items']:

        video = {
            'Id': item['snippet']['resourceId']['videoId'],
            'Title': item['snippet']['title'],
            'Published At': item['snippet']['publishedAt']
        }

        videos.append(video)

    if 'nextPageToken' in response.keys():
        pageToken = response['nextPageToken']
        morePages = True
    else:
        morePages = False

channelId = 'UCgv4dPk_qZNAbUW9WkuLPSA'
metrics = [
    'views',
    'estimatedAdRevenue'
]

today = datetime.date.today()
last_month_today = today.replace(month=today.month-1)
endDate = last_month_today.replace(day=1) - datetime.timedelta(days=2)
startDate = endDate.replace(day=1)
month = endDate.strftime("%B")
year = endDate.strftime("%Y")

chunkedVideos = [videos[i:i+200] for i in range(0, len(videos), 200)]

for chunk in chunkedVideos:

    service = build('youtubeAnalytics', 'v2', credentials=creds)
    response = service.reports().query(
        ids='channel=={0}'.format(channelId),
        metrics=','.join(metrics),
        dimensions='video',
        startDate=startDate,
        endDate=endDate,
        filters='video=={0}'.format(','.join([video['Id'] for video in chunk])),
    ).execute()

    for row in response['rows']:
        id = row[0]
        views = row[1]
        estimatedAdRevenue = row[2]

        for video in videos:
            if video['Id'] == id:
                video['Views'] = views
                video['Estimated Ad Revenue'] = estimatedAdRevenue

df = pd.DataFrame(videos)
df['Link'] = df['Id'].apply(lambda x: 'https://www.youtube.com/watch?v={0}'.format(x))
df['Editor Cut'] = df['Estimated Ad Revenue'].apply(lambda x: x / 10)

output = df[['Title', 'Link', 'Estimated Ad Revenue', 'Editor Cut']].copy()
output['Editor'] = ''
output.drop_duplicates(inplace=True)

summary = pd.DataFrame(columns=['Editor', 'Editor Cut'])
editors = ['Quack', 'Krohnos']
summary['Editor'] = editors
summary['Editor Cut'] = summary['Editor Cut'].index+2
summary['Editor Cut'] = summary['Editor Cut'].apply(lambda x: "=SUMIF('Video List'!$E:E, $A{0}, 'Video List'!$D:$D)".format(x))

filename = 'Ad_Revenue_{0}_{1}.xlsx'.format(month, year)
writer = pd.ExcelWriter(filename, engine='xlsxwriter')
centered_format = writer.book.add_format({'align': 'center', 'valign': 'vcenter'})
money_format = writer.book.add_format({'align': 'center', 'valign': 'vcenter', 'num_format': '$#,##0.00'})

summary.to_excel(writer, sheet_name='Summary', index=False)
worksheet = writer.sheets['Summary']
worksheet.set_column('A:A', 20, centered_format)
worksheet.set_column('B:B', 20, money_format)


output.to_excel(writer, sheet_name='Video List', index=False)
worksheet = writer.sheets['Video List']

for index, column in enumerate(output.columns):
    series = output[column]
    max_length = max((
        series.astype(str).map(len).max(),  # len of largest item
        len(str(series.name))  # len of column name/header
    ))

    if index == 1:
        max_length += 2
    
    if index == 0 or index == 4:
        worksheet.set_column(index, index, max_length, centered_format)
    elif index == 2 or index == 3:
        worksheet.set_column(index, index, max_length, money_format)
    else:    
        worksheet.set_column(index, index, max_length)

writer.save()

try:
    uploader.upload(filename)
    print('Finished uploading {0}!'.format(filename))
except Exception as e:
    print('Error uploading {0}!'.format(filename))
    print(e)