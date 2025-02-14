from marshmallow import (Schema,
                         fields,
                         validates,
                         ValidationError,
                         post_load)


class PaymentSchema(Schema):
    amount = fields.Dict(required=True)
    user_id = fields.Str(required=True)
    order_id = fields.Int(required=True)

    @validates('amount')
    def validate_amount(self, amount: dict) -> None:
        if 'value' not in amount or 'currency' not in amount:
            raise ValidationError('Словарь amount должен содержать'
                                  'поля "value" и "currency".')
        if not isinstance(amount['value'], (str)) or \
           not isinstance(amount['currency'], str):
            raise ValidationError('value и currency должны быть строками.')

    @post_load
    def make_payment(self, data: dict, **kwargs) -> dict:
        return data
