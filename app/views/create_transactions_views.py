from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transactions_model import Transaction
from http import HTTPStatus


transactions = Blueprint("transactions", __name__, url_prefix="/api")


@transactions.route("/transactions/register", methods=["POST"])
@jwt_required()
def create_user():
    session = current_app.db.session
    body = request.get_json()
    user_id = get_jwt_identity()

    date = body.get("date")
    type = body.get("type")
    coin = body.get("coin")
    fiat = body.get("fiat")
    price_per_coin = body.get("price_per_coin")
    quantity = body.get("quantity")
    foreign_exch = body.get("foreign_exch")

    price_usd = price_per_coin if fiat == 'usd' else price_per_coin / 5
    price_brl = price_per_coin if fiat == 'brl' else price_per_coin * 5

    transactions = Transaction.query.filter_by(
        coin=body["coin"], user_id=user_id).order_by(Transaction.date.asc()).all()

    if not transactions:
        avg_price_brl = price_brl
        avg_price_usd = price_usd
        net_quantity = body.get("quantity")

    for transaction in transactions:

        if type == 'buy' or type == 'output':

            net_quantity = transactions[-1].net_quantity
            avg_price_brl = transactions[-1].avg_price_brl
            avg_price_usd = transactions[-1].avg_price_usd

            net_quantity += quantity

            avg_price_brl = ((price_brl * quantity + avg_price_brl *
                             (net_quantity - quantity)) / net_quantity)
            avg_price_usd = ((price_usd * quantity + avg_price_usd *
                             (net_quantity - quantity)) / net_quantity)

        if type == 'sell' or type == 'input':
            net_quantity = transactions[-1].net_quantity
            avg_price_brl = transactions[-1].avg_price_brl
            avg_price_usd = transactions[-1].avg_price_usd

            net_quantity -= quantity

    new_transaction = Transaction(date=date, type=type, coin=coin, fiat=fiat, price_per_coin=price_per_coin, avg_price_brl=avg_price_brl,
                                  avg_price_usd=avg_price_usd, net_quantity=net_quantity, quantity=quantity, foreign_exch=foreign_exch, user_id=user_id)

    session.add(new_transaction)
    session.commit()

    return new_transaction.serialized(), HTTPStatus.CREATED
