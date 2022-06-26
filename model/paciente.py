from marshmallow import Schema, fields

class PacienteSchema(Schema):
    id = fields.UUID(requiered=True)
    nombre = fields.Str(required=True)
    apellido = fields.Str(required=True)
    rut = fields.Str(required=True)
    email = fields.Email(required=True)
    fecha_nacimiento = fields.Date(required=True)
