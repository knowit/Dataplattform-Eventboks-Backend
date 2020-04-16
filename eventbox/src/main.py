import json
import logging
from util.database import create_tables, Session, Event
from util.schemas import eventSchema
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
    # TODO
    return {
        'statusCode': 200,
        'body': 'Hello from update event'
    }

def create_database(event, context):
    create_tables()
