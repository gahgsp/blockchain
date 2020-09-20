from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
wallet = Wallet()
blockchain = Blockchain(wallet.public_key)
CORS(app)


@app.route('/', methods=['GET'])
def get_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        success_response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(success_response), 201
    else:
        error_response = {
            'message': 'An error occurred when saving the keys into the database!'
        }
        return jsonify(error_response), 500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        success_response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(success_response), 201
    else:
        error_response = {
            'message': 'An error occurred when loading the keys into the database!'
        }
        return jsonify(error_response), 500


@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance is not None:
        success_response = {
            'message': 'Successfully retrieved the balance!',
            'balance': balance
        }
        return jsonify(success_response), 200
    else:
        error_response = {
            'message': 'It was not possible to retrieve the balance!',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(error_response), 500


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key is None:
        no_wallet_error_response = {
            'message': 'No wallet correctly setup!'
        }
        return jsonify(no_wallet_error_response), 400
    values = request.get_json()
    if not values:
        no_input_errors_response = {
            'message': 'No necessary data found in the request!'
        }
        return jsonify(no_input_errors_response), 400
    required_fields = ['recipient', 'amount']
    # Checking if the request has at least the two required fields to create a new transaction.
    if not all(field in values for field in required_fields):
        required_errors_response = {
            'message': 'There are required fields missing in the request!'
        }
        return jsonify(required_errors_response), 400
    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(recipient, amount, wallet.public_key, signature)
    if success:
        success_response = {
            'message': 'Successfully added a new transaction!',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(success_response), 201
    else:
        error_response = {
            'message': 'An error occurred while creating a new transaction!'
        }
        return jsonify(error_response), 500


@app.route('/mine', methods=['POST'])
def mine_block():
    block = blockchain.mine_block()
    if block is not None:
        converted_block_to_dict = block.__dict__.copy()
        converted_block_to_dict['transactions'] = [transaction.__dict__ for transaction in
                                                   converted_block_to_dict['transactions']]
        success_response = {
            'message': 'A new block was successfully mined!',
            'block': converted_block_to_dict,
            'funds': blockchain.get_balance()
        }
        return jsonify(success_response), 201
    else:
        error_response = {
            'message': 'It was not possible to mine a new block!',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(error_response), 500


@app.route('/transactions', methods=['GET'])
def get_open_transactions():
    transactions = blockchain.get_open_transactions()
    converted_transactions_to_dict = [transaction.__dict__ for transaction in transactions]
    return jsonify(converted_transactions_to_dict), 200


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.get_chain()
    converted_chain_to_dict = [block.__dict__.copy() for block in chain_snapshot]
    for converted_dict_block in converted_chain_to_dict:
        converted_dict_block['transactions'] = [transaction.__dict__ for transaction in
                                                converted_dict_block['transactions']]
    # The return of the routes is always a tuple: the body of the response and the HTTP code.
    return jsonify(converted_chain_to_dict), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
