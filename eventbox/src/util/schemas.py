from marshmallow import Schema, fields, post_load
# from .database import Event

class _Event(Schema):
    eventname = fields.String()
    creator = fields.String()
    start = fields.DateTime()
    end = fields.DateTime()

    # @post_load
    # def create_event(self, data, **kwargs):
    #     return Event(**data)

class EventRequest(_Event):
    pass

class EventResponse(_Event):
    id = fields.String()
    eventcode = fields.String()
    active = fields.Boolean()

eventRequestSchema = EventRequest()
eventResponseSchema = EventResponse()