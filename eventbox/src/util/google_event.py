import os
import json
import logging
import re
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
import httplib2
import googleapiclient.discovery as api
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials

from .database import Event

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)

def google_sync():
    ssm = boto3.client('ssm')
    credentials = ssm.get_parameter(
        Name='/dev/eventBox/googleCredentials',
        WithDecryption=False
    )
    credentials = json.loads(credentials['Parameter']['Value'])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials, ['https://www.googleapis.com/auth/calendar.readonly'])
    
    calendars = ssm.get_parameter(
        Name='/dev/eventBox/googleCalendarIds',
        WithDecryption=False
    )['Parameter']['Value'].split(',')

    http = credentials.authorize(
        httplib2.Http()
    )

    service = api.build(
        serviceName='calendar',
        version='v3',
        http=http,
        cache_discovery=False
    )

    events = []

    for calendar in calendars:
        calendar_id = re.compile('.*_(.*)@.*').findall(calendar)[0]

        try:
            syncToken = ssm.get_parameter(
                Name='/dev/eventBox/' + calendar_id,
                WithDecryption = False
            )['Parameter']['Value']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                syncToken = None
            else:
                raise e

        requestParams = dict(
            calendarId=calendar,
            singleEvents=True,
        )

        res, nextSyncToken = _sync(service, syncToken, **requestParams)

        events.extend(res)
        ssm.put_parameter(
            Name='/dev/eventBox/' + calendar_id,
            Value=nextSyncToken,
            Type='String',
            Overwrite=True
        )

    return events



def _sync(service, syncToken, **requestParams):
    pageToken = None
    res = []

    _logger.info(syncToken)

    if not syncToken:
        requestParams['timeMin'] = '2019-01-01T00:00:00+00:00'

    while True:
        requestParams['pageToken'] = pageToken
        try:
            page = service.events().list(
                syncToken=syncToken, 
                **requestParams
            ).execute()
        except HttpError as e:
            if e.resp.status == 410:
                _logger.info('Sync Token expired')
                return _sync(service, None, **requestParams)


        for item in page['items']:
            try:
                e = Event(
                    eventname=item['summary'],
                    creator=item['creator']['email'],
                    start=_getdate(item['start']),
                    end=_getdate(item['end']),
                    isgoogle=True
                )
                res.append(e)
            except KeyError:
                _logger.info('Ignoring item: {}'.format(item))
        
        pageToken = page.get('nextPageToken')

        if not pageToken:
            break
    
    return (res, page['nextSyncToken'])

def _getdate(item):
    if 'dateTime' in item:
        return item['dateTime']
    elif 'date' in item:
        return item['date'] + 'T00:00+02:00'
    else:
        _logger.info('Could not find date')
        raise KeyError