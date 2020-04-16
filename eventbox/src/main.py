import json
import logging
from util.database import create_tables, Session, Event
from util.schemas import eventSchema
from sqlalchemy.orm.exc import UnmappedInstanceError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_events(e, context):
    session = Session()
    creator = json.loads(e['body'])['creator']
    result = session.query(Event).filter(Event.creator == creator)
    session.close()
    return {
        'statusCode': 200,
        'body': eventSchema.dumps(result, many=True)
    }

def get_event(e, context):
    event_id = e['pathParameters']['id']

    session = Session()
    result = session.query(Event).filter(Event.id == event_id).first()
    session.close()
    
    return {
        'statusCode': 200,
        'body': eventSchema.dumps(result)
    }

def add_event(e, context):
    body = eventSchema.loads(e['body'])
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
    event = eventSchema.loads(e['body'])
   
    session = Session()
    session.delete(event)
    session.commit()
    session.close()
    return {
        'statusCode': 200,
        'body': 'Event successfully deleted'
    }

def update_event(e, context):
    event_id = e['pathParameters']['id']
    session = Session()
    event = session.query(Event).filter(Event.id == event_id).first()
    try:
        body = eventSchema.loads(e['body'])
        event.creator = body["creator"]
        event.start = body["start"]
        event.end = body["end"]
        event.eventcode = body["eventcode"]
        event.active = body["active"]
        session.commit()
    except (UnmappedInstanceError, AttributeError):
        return{
            'statusCode' : 404,
            'body' : 'Event with ID ' + str(event_id) + ' not found'
        } 
    session.close()
    return {
        'statusCode': 200,
        'body': 'Event with ID ' + str(event_id) + ' successfully updated'
    }

def create_database(event, context):
    create_tables()
