from marshmallow import (Schema,
                         fields,
                         validates_schema,
                         ValidationError,
                         post_load)


class PaymentSchema(Schema):
    amount = fields.Dict(required=True)
    user_id = fields.Str(required=True)
    order_id = fields.Int(required=True)

    @validates_schema
    def validate_amount(self, data, **kwargs):
        amount = data.get('amount')
        if not amount or 'value' not in amount or 'currency' not in amount:
            raise ValidationError(
                'Словарь amount должен содержать "value" и "currency":',
                field_name='amount'
            )
        if not all(isinstance(amount[k], str) for k in ('value', 'currency')):
            raise ValidationError(
                'value и currency должны быть строками.',
                field_name='amount'
            )

    @post_load
    def make_payment(self, data: dict, **kwargs) -> dict:
        return data


class RefundSchema(Schema):
    amount = fields.Dict(required=True)
    user_id = fields.Str(required=True)
    payment_id = fields.Str(required=True)

    @validates_schema
    def validate_amount(self, data, **kwargs):
        amount = data.get('amount')
        if not amount or 'value' not in amount or 'currency' not in amount:
            raise ValidationError(
                'Словарь amount должен содержать поля "value" и "currency".',
                field_name='amount'
            )
        if not all(isinstance(amount[k], str) for k in ('value', 'currency')):
            raise ValidationError(
                '"value" и "currency" должны быть строками.',
                field_name='amount'
            )

    @post_load
    def make_payment(self, data: dict, **kwargs) -> dict:
        return data
