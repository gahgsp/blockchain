from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from blockchain import Blockchain
from wallet import Wallet

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
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
        blockchain = Blockchain(wallet.public_key, port)
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


@app.route('/broadcast', methods=['POST'])
def broadcast_transaction():
    values = request.get_json()
    if not values:
        no_data_error_response = {
            'message': 'No data found to broadcast!'
        }
        return jsonify(no_data_error_response), 400
    required_fields = ['sender', 'recipient', 'amount', 'signature']
    if not all(value in values for value in required_fields):
        required_errors_response = {
            'message': 'There are required fields missing in the request!'
        }
        return jsonify(required_errors_response), 400
    success = blockchain.add_transaction(values['recipient'], values['amount'], values['sender'], values['signature'],
                                         True)
    if success:
        success_response = {
            'message': 'Successfully added a new transaction!',
            'transaction': {
                'sender': values['sender'],
                'recipient': values['recipient'],
                'amount': values['amount'],
                'signature': values['signature']
            }
        }
        return jsonify(success_response), 201
    else:
        error_response = {
            'message': 'An error occurred while creating a new transaction!'
        }
        return jsonify(error_response), 500


@app.route('/broadcastBlock', methods=['POST'])
def broadcast_block():
    values = request.get_json()
    if not values:
        no_data_error_response = {
            'message': 'No data found to broadcast!'
        }
        return jsonify(no_data_error_response), 400
    if 'block' not in values:
        required_errors_response = {
            'message': 'There are required fields missing in the request!'
        }
        return jsonify(required_errors_response), 400
    block = values['block']
    if block['index'] == blockchain.get_chain()[-1].index + 1:
        if blockchain.add_block(block):
            success_response = {
                'message': 'The Block was successfully added to the Blockchain!'
            }
            return jsonify(success_response), 200
        else:
            error_response = {
                'message': 'The Block was not successfully added to the Blockchain!'
            }
            return jsonify(error_response), 409
    elif block['index'] > blockchain.get_chain()[-1].index:
        response = {
            'message': 'The current Blockchain seems to differ from the local Blockchain. The Block was not added!'
        }
        blockchain.resolve_conflicts = True
        return jsonify(response), 200
    else:
        response = {
            'message': 'The current Blockchain seems to be shorter than the expected. The Block was not added!'
        }
        return jsonify(response), 409


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
    if blockchain.resolve_conflicts:
        conflict_error_response = {
            'message': 'You need to resolve the conflicts first! The Block was not mined!'
        }
        return jsonify(conflict_error_response), 409

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


@app.route('/resolveConflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {
            'message': 'The Blockchain was replaced!'
        }
    else:
        response = {
            'message': 'The Local Blockchain was kept!'
        }
    return jsonify(response), 200


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


@app.route('/node', methods=['POST'])
def add_node():
    values = request.get_json()
    if not values:
        no_input_errors_response = {
            'message': 'No necessary data found in the request!'
        }
        return jsonify(no_input_errors_response), 400
    if 'node' not in values:
        required_errors_response = {
            'message': 'The node to be added is missing in the request!'
        }
        return jsonify(required_errors_response), 400
    node = values['node']
    blockchain.add_peer_node(node)
    success_response = {
        'message': 'The node was added successfully!',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(success_response), 201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url is None:
        param_error_response = {
            'message': 'You must provide a node URL to be deleted!'
        }
        return jsonify(param_error_response), 400
    blockchain.remove_peer_node(node_url)
    success_response = {
        'message': 'The node was successfully removed!',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(success_response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    app.run(host='0.0.0.0', port=port)
