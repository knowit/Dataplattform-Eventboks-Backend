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
_ssm = boto3.client('ssm')

def get_google_service():
    credentials = _ssm.get_parameter(
        Name='/dev/eventBox/googleCredentials',
        WithDecryption=False
    )
    credentials = json.loads(credentials['Parameter']['Value'])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials, ['https://www.googleapis.com/auth/calendar.readonly'])

    http = credentials.authorize(
        httplib2.Http()
    )

    return api.build(
        serviceName='calendar',
        version='v3',
        http=http,
        cache_discovery=False
    )


def get_google_calendars():
    return _ssm.get_parameter(
        Name='/dev/eventBox/googleCalendarIds',
        WithDecryption=False
    )['Parameter']['Value'].split(',')

def get_google_synctoken(calendar_id):
    try:
        syncToken = _ssm.get_parameter(
            Name='/dev/eventBox/' + calendar_id,
            WithDecryption = False
        )['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            syncToken = None
        else:
            raise e
        
    return syncToken


def set_google_synctoken(calendar_id, syncToken):
    _ssm.put_parameter(
        Name='/dev/eventBox/' + calendar_id,
        Value=syncToken,
        Type='String',
        Overwrite=True
    )


def sync(service, syncToken, **requestParams):
    pageToken = None
    res = []

    _logger.info(syncToken)

    if not syncToken:
        requestParams['timeMin'] = '2019-01-01T00:00:00+00:00'

    while True:
        requestParams['pageToken'] = pageToken
        page = service.events().list(
            syncToken=syncToken, 
            **requestParams
        ).execute()

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