



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
channelId = ''
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
#print(json.dumps(response, indent=2))

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

    #print(json.dumps(response, indent=2))
    
    video = {}
    for item in response['items']:

        video = {
            'Id': item['snippet']['resourceId']['videoId'],
            'Title': item['snippet']['title'],
            'Published At': item['snippet']['publishedAt'],
            #'description': item['snippet']['description']
        }

        #print(video)
        #input()

        videos.append(video)
        #[print(video['title']) for video in videos]

    if 'nextPageToken' in response.keys():
        params['pageToken'] = response['nextPageToken']
        morePages = True
    else:
        morePages = False

endpoint = 'https://youtubeanalytics.googleapis.com/v2/reports'
channelId = ''

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
        'startDate': '2021-10-01',
        'endDate': '2021-10-31',
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

output = df[['Title', 'Link', 'Estimated Ad Revenue']].copy()

path = 'output.xlsx'

output.to_excel(path, index=False)
