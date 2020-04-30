import json
import logging
import re

from util.database import create_tables, Session, Event
from util.schemas import eventSchema
from util.google_event import sync, get_google_service, get_google_calendars, get_google_synctoken, set_google_synctoken, HttpError

from util.schemas import eventRequestSchema, eventResponseSchema
from sqlalchemy.orm.exc import UnmappedInstanceError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_events(e, context):
    # TODO: Should filter by creator
    session = Session()
    result = session.query(Event).all()
    session.close()
    return {
        'statusCode': 200,
        'body': eventResponseSchema.dumps(result, many=True)
    }


def get_event(e, context):
    event_id = e['pathParameters']['id']

    session = Session()
    result = session.query(Event).filter(Event.id == event_id).first()
    session.close()

    return {
        'statusCode': 200,
        'body': eventResponseSchema.dumps(result)
    }


def add_event(e, context):
    body = eventRequestSchema.loads(e['body'])
    logger.info(body)
    event = Event(**body)

    session = Session()
    session.add(event)
    session.commit()
    session.close()

    return {
        'statusCode': 200,
        'body': 'Success'
    }


def delete_event(e, context):
    event_id = e['pathParameters']['id']
    session = Session()
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        session.delete(event)
        session.commit()
        session.close()
    except UnmappedInstanceError:
        return{
            'statusCode' : 404,
            'body' : 'Event with ID ' + str(event_id) + ' not found'
        } 
    return {
        'statusCode': 200,
        'body': 'Event with ID ' + str(event_id) + ' successfully deleted'
    }


def update_event(e, context):
    event_id = e['pathParameters']['id']
    session = Session()
    body = eventRequestSchema.loads(e['body'])
    res = session.query(Event).filter(Event.id == event_id).update(body)
    session.commit()
    session.close()
    if res > 0:
        return {
            'statusCode': 200,
            'body': 'Event with ID ' + str(event_id) + ' successfully updated'
        }
    return {
        'statusCode': 404,
        'body': 'Event with ID ' + str(event_id) + ' not found'
    }


def create_database(event, context):
    create_tables()


def sync_google(event, context):
    session = Session()
    
    service = get_google_service()
    calendars = get_google_calendars()

    for calendar in calendars:
        calendar_id = re.compile('.*_(.*)@.*').findall(calendar)[0]
        syncToken = get_google_synctoken(calendar_id)

        if not syncToken:
            logger.info('No sync token found, deleting entries')
            session.query(Event).filter(Event.google_calendar_id == calendar_id).delete()


        requestParams = dict(
            calendarId=calendar,
            singleEvents=True,
        )

        try:
            res, nextSyncToken = sync(service, syncToken, **requestParams)
        except HttpError as e:
            if e.resp.status == 410:
                # Do full sync
                _logger.info('Sync Token expired, do full sync')
                session.query(Event).filter(Event.google_calendar_id == calendar_id).delete()
                res, nextSyncToken = sync(service, None, **requestParams)

        res, nextSyncToken = sync(service, syncToken, **requestParams)

        for item in res:
            item.google_calendar_id = calendar_id
        
        session.add_all(res)
        session.commit()
        
        set_google_synctoken(calendar_id, nextSyncToken)

    session.close()


def verify_eventcode(e, context):
    event_code = e['pathParameters']['eventcode']
    session = Session()
    event = session.query(Event).filter(Event.eventcode == event_code).filter(Event.active).first()
    session.close()
    if not event:
        return{
            'statusCode': 404,
            'body': 'Event with eventcode ' + str(event_code) + ' not found'
        }
    return{
        'statusCode': 200,
        'body': eventResponseSchema.dumps(event)
    }
