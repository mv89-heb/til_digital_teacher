from marshmallow import Schema, fields

submit_answer_schema = Schema.from_dict({"answer_id": fields.Integer(required=True)})()
