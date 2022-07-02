



import uploader
import pandas as pd
import datetime
from os import path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/yt-analytics-monetary.readonly',
    'https://www.googleapis.com/auth/youtube',
    #'https://www.googleapis.com/auth/youtubepartner',
]
creds = None

creds_file = 'secrets/quack_credentials.json'
creds_file = 'secrets/krohnos_creds.json'

if path.exists(creds_file):
    creds = Credentials.from_authorized_user_file(creds_file, SCOPES)

if (not creds or not creds.valid) or True:
    if (creds and creds.expired and creds.refresh_token) or True:
        print('refreshing creds')
        creds.refresh(Request())
    else:
        print('existing creds')
        flow = InstalledAppFlow.from_client_secrets_file(
            'secrets/google_project_credentials.json', SCOPES)
        #creds = flow.run_local_server(port=0)
        creds = flow.run_console()
    # Save the credentials for the next run
    with open(creds_file, 'w') as token:
        token.write(creds.to_json())
    

playlistId = 'UUgv4dPk_qZNAbUW9WkuLPSA' # main
playlistId = 'UUdBXOyqr8cDshsp7kcKDAkg' # clips

endpoint = 'https://www.googleapis.com/youtube/v3/playlistItems'
parts = [
    'snippet',
    'contentDetails'
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

    requestVideo = {}
    for item in response['items']:

        requestVideo = {
            'Id': item['snippet']['resourceId']['videoId'],
            'Title': item['snippet']['title'],
            'Published At': item['snippet']['publishedAt'],
        }

        try: 
            requestVideo['Editor'] = item['snippet']['description'].split('Edited by')[1].split('|')[0].strip().lower()
            requestVideo['Editor'] = requestVideo['Editor'] = '' if requestVideo['Editor'] == '[name]' else requestVideo['Editor']
        except:
            requestVideo['Editor'] = ''
            #print(item['snippet']['description'])
        
        #requestVideo['Editor'] = input()

        #input()

        videos.append(requestVideo)

    if 'nextPageToken' in response.keys():
        pageToken = response['nextPageToken']
        morePages = True
    else:
        morePages = False


#channelId = 'UCgv4dPk_qZNAbUW9WkuLPSA' # main
channelId = 'UCdBXOyqr8cDshsp7kcKDAkg' # clips

metrics = [
    'views',
    'estimatedRevenue',
]

today = datetime.date.today() + datetime.timedelta(days=31)
last_month_today = today.replace(month=today.month-2)
endOfMonth = last_month_today.replace(day=1) - datetime.timedelta(days=1)
startOfMonth = endOfMonth.replace(day=1)
month = endOfMonth.strftime("%B")
year = endOfMonth.strftime("%Y")


editors = []

for video in videos[:]:

    videoUploadDate = datetime.datetime.strptime(video['Published At'], "%Y-%m-%dT%H:%M:%S%z").date()
    thirtyDayCutoff = videoUploadDate + datetime.timedelta(days=30)

    if videoUploadDate < startOfMonth or videoUploadDate > endOfMonth:
        #print('Video not in current month')
        videos.remove(video)
        continue

    #print('https://youtube.com/watch?v={0} - {1}'.format(video['Id'], video['Title']))

    video['Upload Date'] = videoUploadDate
    video['Cutoff Date'] = thirtyDayCutoff


    print(video)
    #input()

    if video['Editor'] not in editors and video['Editor'] != '':
        editors.append(video['Editor'])


print('{0} videos found'.format(len(videos)))


#[print(video['Id']) for video in videos]
#exit()



print('getting videos from {0} to {1}'.format(startOfMonth, endOfMonth))




df = pd.DataFrame(videos)
print(df)
df['Link'] = df['Id'].apply(lambda x: 'https://www.youtube.com/watch?v={0}'.format(x))
#df['Editor Cut'] = df['Estimated Revenue'].apply(lambda x: x / 10)
df['Estimated Revenue'] = -99999
df['Editor Cut'] = 0
df['Upload Date'] = df['Upload Date'].apply(lambda x: x.strftime("%Y-%m-%d"))
df['Cutoff Date'] = df['Cutoff Date'].apply(lambda x: x.strftime("%Y-%m-%d"))
#df['Verify'] = '=HYPERLINK("https://studio.youtube.com/video/{0}/analytics/tab-earn_revenue/period-default?c=UCdBXOyqr8cDshsp7kcKDAkg", "Link")'.format(df['Id'])
df['Verify'] = df['Id'].apply(lambda x: 'https://studio.youtube.com/video/{0}/analytics/tab-earn_revenue/period-default?c={1}'.format(x, channelId))
df['Verify'] = df['Verify'].apply(lambda x: '=HYPERLINK("{0}", "Link")'.format(x))

print(df)

output = df[['Title', 'Link', 'Estimated Revenue', 'Editor Cut', 'Upload Date', 'Cutoff Date']].copy()
output['Editor'] = df['Editor']
output['Verify'] = df['Verify']
output.drop_duplicates(inplace=True)

summary = pd.DataFrame(columns=['Editor', 'Editor Cut'])
#editors = ['quack', 'imbryguy', 'zinjo', 'kaage', 'erik', 'connor']
summary['Editor'] = editors
summary['Editor Cut'] = summary['Editor Cut'].index+2
summary['Editor Cut'] = summary['Editor Cut'].apply(lambda x: "=SUMIF('Video List'!$G:G, $A{0}, 'Video List'!$D:$D)".format(x))

#filename = 'output/temp_{0}_{1}.xlsx'.format(month, year)
#filename = 'output/clip_test_{0}_{1}.xlsx'.format(month, year)
#filename = 'dev/Clip_Revenue_{0}_{1}.xlsx'.format(month, year)
filename = 'dev/Editor_Revenue_{0}_{1}.xlsx'.format(month, year)

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
worksheet.set_column('H:H', 20, centered_format)

writer.save()

try:
    #uploader.upload(filename)
    print('Finished uploading {0}!'.format(filename))
except Exception as e:
    print('Error uploading {0}!'.format(filename))
    print(e)