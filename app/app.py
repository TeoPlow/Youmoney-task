import logging
from flask import Flask, request
from flask_restful import Api, Resource
from marshmallow import ValidationError
from yookassa.domain.exceptions.not_found_error import NotFoundError
from yookassa.domain.exceptions.bad_request_error import BadRequestError
from http import HTTPStatus
from models import (
    create_payment,
    check_payment,
    # recheck_payments_status,
    refund_payment
)
from schemas import PaymentSchema, RefundSchema
from db import init_db, add_payment
from config import API_HOST, API_PORT

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
        try:
            payment_info = check_payment(payment_id)
            return payment_info.json(), HTTPStatus.OK

        except NotFoundError as e:
            message = f'Платёж {payment_id} не найден'
            log.warning(message)
            return {"type": "warning",
                    "message": message,
                    "log": str(e)}, HTTPStatus.NOT_FOUND

        except Exception as e:
            message = ('Ошибка при получении информации о платеже '
                       f'{payment_id}')
            log.error(message)
            return {"type": "error",
                    "message": message,
                    "log": e}, HTTPStatus.INTERNAL_SERVER_ERROR


class PaymentCreateResource(Resource):
    def post(self) -> tuple[dict, HTTPStatus]:
        """
        Совершает платеж через YooKassa.
        :param request: запрос с данными платежа.
        :return: URL для переадресации на страницу оплаты.
        """
        log.debug(f'POST: Создание платежа - {request.json}')
        try:
            data = request.json
            schema = PaymentSchema()
            valid_data = schema.load(data)
            payment_url, payment_id = create_payment(valid_data)
            add_payment(payment_id,
                        valid_data['order_id'],
                        valid_data['user_id'],
                        status='pending')
            return {'confirmation_url': payment_url}, HTTPStatus.CREATED
        except ValidationError as e:
            message = f'Ошибка валидации - {e.messages}'
            log.error(message)
            return {"type": "error",
                    "message": message,
                    "log": e}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            message = 'Ошибка при создании платежа'
            log.error(message)
            return {"type": "error",
                    "message": message,
                    "log": e}, HTTPStatus.INTERNAL_SERVER_ERROR
        

class RefundCreateResource(Resource):
    def post(self) -> tuple[dict, HTTPStatus]:
        """
        Делает возврат средств пользователю через YooKassa
        :param request: запрос с данными для возврата.
        :return: информация о возврате.
        """
        log.debug(f'POST: Возврат средств - {request.json}')
        try:
            data = request.json
            schema = RefundSchema()
            valid_data = schema.load(data)
            refund_data = refund_payment(valid_data)
            return refund_data, HTTPStatus.CREATED
        except ValidationError as e:
            message = f'Ошибка валидации - {e.messages}'
            log.error(message)
            return {"type": "error",
                    "message": message,
                    "log": e}, HTTPStatus.BAD_REQUEST
        except BadRequestError as e:
            message = 'Неверный запрос. Вероятно ошибка в ID платежа.'
            return {"type": "error",
                    "message": message,
                    "log": e}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            message = 'Ошибка при возврате платежа'
            log.error(message)
            return {"type": "error",
                    "message": message,
                    "log": e}, HTTPStatus.INTERNAL_SERVER_ERROR


api.add_resource(PaymentCreateResource, '/api/payment')
api.add_resource(PaymentResource, '/api/payment/<string:payment_id>')
api.add_resource(RefundCreateResource, '/api/refund')


if __name__ == '__main__':
    init_db()
    # recheck_payments_status()
    app.run(host=API_HOST, port=API_PORT, debug=True)
