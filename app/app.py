import logging
from flask import Flask, request
from flask_restful import Api, Resource
from marshmallow import ValidationError
from http import HTTPStatus
from models import (
    create_payment,
    check_payment,
    recheck_payments_status
)
from schemas import PaymentSchema
from db import init_db, add_payment

app = Flask(__name__)
api = Api(app)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class PaymentResource(Resource):
    def get(self, payment_id: str) -> tuple[dict, HTTPStatus]:
        """
        Возвращает информацию о платеже.
        :param payment_id: идентификатор платежа.
        :return: словарь с информацией о платеже.
        """
        log.debug(f'GET: Запрос информации о платеже {payment_id}')
        payment_info = check_payment(payment_id)
        return payment_info.json(), HTTPStatus.OK


class PaymentCreateResource(Resource):
    def post(self) -> tuple[dict, HTTPStatus]:
        """
        Совершает платеж через YooKassa.
        :param request: запрос с данными платежа.
        :return: URL для переадресации на страницу оплаты.
        """
        log.debug(f'POST: Создание платежа - {request.json}')
        data = request.json
        schema = PaymentSchema()
        try:
            valid_data = schema.load(data)
        except ValidationError as exc:
            log.error(f'Ошибка валидации - {exc.messages}')
            return exc.messages, HTTPStatus.BAD_REQUEST

        payment_url, payment_id = create_payment(valid_data)
        add_payment(payment_id,
                    valid_data['order_id'],
                    valid_data['user_id'],
                    status='pending')
        return {'confirmation_url': payment_url}, HTTPStatus.CREATED


api.add_resource(PaymentCreateResource, '/api/payment')
api.add_resource(PaymentResource, '/api/payment/<string:payment_id>')


if __name__ == '__main__':
    recheck_payments_status()
    init_db()
    app.run(debug=True)
