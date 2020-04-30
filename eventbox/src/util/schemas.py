from marshmallow import Schema, fields, post_load

class _Event(Schema):
    eventname = fields.String()
    creator = fields.String()
    start = fields.DateTime()
    end = fields.DateTime()


class EventRequest(_Event):
    pass

class EventResponse(_Event):
    id = fields.String()
    eventcode = fields.String()
    active = fields.Boolean()
    isgoogle = fields.Boolean()

eventRequestSchema = EventRequest()
eventResponseSchema = EventResponse()
