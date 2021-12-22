



from os import write
import numpy
import pandas as pd
import re
import json
import requests
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import configparser

config = configparser.ConfigParser()
config.read_file(open('config.cfg'))
token = config.get('Tokens', 'Bearer')

CLIENT_SECRETS_FILE = 'client_secret.json'


API_SERVICE_NAME = 'youtubereporting'
API_VERSION = 'v1'

endpoint = 'https://www.googleapis.com/youtube/v3/playlists'
channelId = 'UUgv4dPk_qZNAbUW9WkuLPSA'
parts = ','.join([
    'id'
])

auth = {
    'Authorization': 'Bearer {0}'.format(token)
}

params = {
    'id' : channelId,
    'part': parts
}

response = requests.get(endpoint, params=params, headers=auth).json()

playlistId = response['items'][0]['id']

endpoint = 'https://www.googleapis.com/youtube/v3/playlistItems'
parts = [
    'snippet',
    #'contentDetails'
]

params = {
    'playlistId': playlistId,
    'part': parts,
    'maxResults': 50,
    'pageToken': ''
}

videos = []

morePages = True

while morePages:

    response = requests.get(endpoint, params=params, headers=auth).json()

    video = {}
    for item in response['items']:

        video = {
            'Id': item['snippet']['resourceId']['videoId'],
            'Title': item['snippet']['title'],
            'Published At': item['snippet']['publishedAt']
        }

        videos.append(video)

    if 'nextPageToken' in response.keys():
        params['pageToken'] = response['nextPageToken']
        morePages = True
    else:
        morePages = False

endpoint = 'https://youtubeanalytics.googleapis.com/v2/reports'
channelId = 'UCgv4dPk_qZNAbUW9WkuLPSA'

metrics = [
    'views',
    'estimatedAdRevenue'
]

chunkedVideos = [videos[i:i+200] for i in range(0, len(videos), 200)]

for chunk in chunkedVideos:
    params = {
        'ids': 'channel=={0}'.format(channelId),
        'metrics': ','.join(metrics),
        'dimensions': 'video',
        'startDate': '2021-12-01',
        'endDate': '2021-12-31',
        'filters': 'video=={0}'.format(','.join([video['Id'] for video in chunk])),
    }

    response = requests.get(endpoint, params=params, headers=auth).json()

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
output.drop_duplicates(inplace=True)

summary = pd.DataFrame(columns=['Editor', 'Editor Cut'])
editors = ['Quack', 'Krohnos']
summary['Editor'] = editors
#summary['Editor Cut'] = '=SUMIF(\'Video List\'!$E:$E, $A{0}, \'Video List\'!$D:$D)'
summary['Editor Cut'] = summary['Editor Cut'].index+2
summary['Editor Cut'] = summary['Editor Cut'].apply(lambda x: "=SUMIF('Video List'!$E:E, $A{0}, 'Video List'!$D:$D)".format(x))
#'Video List\'!$E:$E, $A{0}, \'Video List\'!$D:$D)'


writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')

summary.to_excel(writer, sheet_name='Summary', index=False)
output.to_excel(writer, sheet_name='Video List', index=False)

writer.save()

print(output)
print(summary)
