from marshmallow import Schema, fields

class RecetaSchema(Schema):
    id = fields.UUID(requiered=True)
    comentario = fields.Str(required=True)
    farmacos = fields.Str(required=True)
    doctor = fields.Str(required=True)
    paciente_id = fields.UUID(required=True)

