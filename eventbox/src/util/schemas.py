from marshmallow import Schema, fields, post_load

class _EventSchema(Schema):
    id = fields.String()
    eventname = fields.String()
    creator = fields.String()
    start = fields.DateTime()
    end = fields.DateTime()
    eventcode = fields.String()
    active = fields.Boolean()
    isgoogle = fields.Boolean()


eventSchema = _EventSchema()