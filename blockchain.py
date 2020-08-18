# Initializing our blockchain list
MINING_REWARD = 10

genesis_block = {'previous_hash': '', 'index': 0, 'transactions': []}
blockchain = [genesis_block]
open_transactions = []

owner = 'Kelvin'
participants = {'Kelvin'}


def hash_block(block):
    return '#'.join([str(block[key]) for key in block])


def get_balance(participant):
    tx_sender = [[tx['amount'] for tx in block['transactions'] if tx['sender'] == participant] for block in blockchain]
    open_tx_sender = [tx['amount'] for tx in open_transactions if tx['sender'] == participant]
    tx_sender.append(open_tx_sender)
    amount_sent = 0
    for tx in tx_sender:
        if len(tx) > 0:
            amount_sent += tx[0]

    tx_recipient = [[tx['amount'] for tx in block['transactions'] if tx['recipient'] == participant] for block in
                    blockchain]
    amount_received = 0
    for tx in tx_recipient:
        if len(tx) > 0:
            amount_received += tx[0]

    return amount_received - amount_sent


def get_last_blockchain_value():
    """ Returns the last value of the current blockchain. """
    if len(blockchain) < 1:
        return None
    return blockchain[-1]


def verify_transaction(transaction):
    sender_balance = get_balance(transaction['sender'])
    return sender_balance >= transaction['amount']


def add_transaction(recipient, amount=1.0, sender=owner):
    """ Appends a new value as well as the last blockchain to the blockchain.
        :argument sender The sender of the coins.
        :argument recipient The recipient of the coins.
        :argument amount The amount of coins (default[1])
    """
    transaction = {'sender': sender, 'recipient': recipient, 'amount': amount}
    if verify_transaction(transaction):
        open_transactions.append(transaction)
        participants.add(sender)
        participants.add(recipient)
        return True
    return False


def mine_block():
    """ Mines a new block in the blockchain. """
    last_block = blockchain[-1]
    hashed_block = hash_block(last_block)
    reward_transaction = {'sender': 'MINING', 'recipient': owner, 'amount': MINING_REWARD}
    copied_transactions = open_transactions[:]  # Creates a new list with all the values from the original list
    copied_transactions.append(reward_transaction)
    block = {'previous_hash': hashed_block, 'index': len(blockchain), 'transactions': copied_transactions}
    blockchain.append(block)
    return True


def get_transaction_value():
    """ Returns the input of the user (a new transaction amount) as a float. """
    tx_recipient = input('Enter the recipient of the transaction:')
    tx_amount = float(input('Your transaction amount, please:'))
    return tx_recipient, tx_amount


def get_user_choice():
    """ Returns the input from the user. """
    return input('Your choice: ')


def print_blockchain_elements():
    """ Print all the blockchain elements. """
    print('-' * 20 + ' Printing elements ' + '-' * 20)
    for block in blockchain:
        print('Outputting Block')
        print(block)
    else:
        print('-' * 59)


def verify_chain():
    """ Verifies if the blockchain was not manipulated. """
    # When enumerating a list, it returns a pair of index and value (tuple)
    for (index, block) in enumerate(blockchain):
        if index == 0:  # Genesis block
            continue
        if block['previous_hash'] != hash_block(blockchain[index - 1]):
            return False
    return True


def verify_transactions():
    return all([verify_transaction(tx) for tx in open_transactions])


waiting_for_input = True

while waiting_for_input:
    print('Please choose an option: ')
    print('1: Add a new transaction value')
    print('2: Mine a new block')
    print('3: Output the blockchain blocks')
    print('4: Manipulate the blockchain')
    print('5: Output participants')
    print('6: Check transactions validity')
    print('9: Quit')
    user_choice = get_user_choice()
    if user_choice == '1':
        tx_data = get_transaction_value()
        recipient, amount = tx_data
        if add_transaction(recipient, amount):
            print('Transaction has been added successfully!')
        else:
            print('The transaction has failed!')
        print(open_transactions)
    elif user_choice == '2':
        if mine_block():
            open_transactions = []
    elif user_choice == '3':
        print_blockchain_elements()
    elif user_choice == '4':
        if len(blockchain) >= 1:
            blockchain[0] = {'previous_hash': '', 'index': 0, 'transactions': [{'sender': 'Anonymous', 'recipient': 'Anonymous', 'amount': 999}]}
    elif user_choice == '5':
        print(participants)
    elif user_choice == '6':
        if verify_transactions():
            print('All transactions are valid!')
        else:
            print('There are invalid transactions!')
    elif user_choice == '9':
        waiting_for_input = False
    else:
        print('Input was invalid, please, choose a value from the list!')

    # After each action, we verify if the chain was not manipulated
    if not verify_chain():
        print('Invalid blockchain!')
        waiting_for_input = False
    print(get_balance('Kelvin'))
print('Done!')
