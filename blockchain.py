import json
from functools import reduce

import hash_util
from block import Block
from transaction import Transaction
from verification import Verification

# Initializing our blockchain list
MINING_REWARD = 10

blockchain = []
open_transactions = []

owner = 'Kelvin'


def load_data():
    global blockchain
    global open_transactions
    try:
        with open('blockchain.txt', mode='r') as f:
            file_content = f.readlines()
            blockchain = json.loads(file_content[0][:-1])
            updated_blockchain = []
            for block in blockchain:
                converted_transaction = [Transaction(tx['sender'], tx['recipient'], tx['amount']) for tx in
                                         block['transactions']]
                updated_block = Block(block['index'],
                                      block['previous_hash'],
                                      converted_transaction,
                                      block['proof'],
                                      block['timestamp'])
                updated_blockchain.append(updated_block)
            blockchain = updated_blockchain
            open_transactions = json.loads(file_content[1])
            updated_transactions = []
            for transaction in open_transactions:
                updated_transaction = Transaction(transaction['sender'], transaction['recipient'],
                                                  transaction['amount'])
                updated_transactions.append(updated_transaction)
            open_transactions = updated_transactions
    except IOError:
        print('File not found! Initializing the Blockchain with default values...')
        # Starting block for the blockchain
        genesis_block = Block(0, '', [], 100, 0)
        # Adding the starting block to the blockchain
        blockchain = [genesis_block]
        # Initializing the open transactions as an empty list
        open_transactions = []


load_data()


def save_data():
    """
    Saves the current state of the blockchain plus its open transactions to a file.
    """
    try:
        with open('blockchain.txt', mode='w') as f:
            saveable_chain = [block.__dict__ for block in [
                Block(bl.index, bl.previous_hash, [tx.__dict__ for tx in bl.transactions], bl.proof, bl.timestamp) for
                bl in blockchain]]
            f.write(json.dumps(saveable_chain))
            f.write('\n')
            saveable_transactions = [transaction.__dict__ for transaction in open_transactions]
            f.write(json.dumps(saveable_transactions))
    except IOError:
        print('Saving failed!')


def proof_of_work():
    """
    Generates a proof of work for the open transactions, based on the last hashed block which is guessed until it fits.
    :return: a valid number for the proof of work.
    """
    last_block = blockchain[-1]
    last_hash = hash_util.hash_block(last_block)
    proof = 0
    verifier = Verification()
    while not verifier.valid_proof(open_transactions, last_hash, proof):
        proof += 1
    return proof


def get_balance(participant):
    """
    Calculates the current balance for a participant.
    :param participant: the person which we will calculate the balance.
    :return: the total balance of the participant.
    """
    # Fetches all the sent coins for the given person.
    # This fetches the sent amounts of transactions that were already included in the blockchain.
    tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participant] for block in blockchain]
    # This fetches the sent amounts of open transactions (to avoid double spending).
    open_tx_sender = [tx.amount for tx in open_transactions if tx.sender == participant]
    tx_sender.append(open_tx_sender)
    amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)

    # Fetches all the received coins for the given person.
    # This does not consider open transactions because we can not spend the coins
    # before the transactions was confirmed and add to the blockchain.
    tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participant] for block in
                    blockchain]
    amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0,
                             tx_recipient, 0)

    # Calculates and return the balance.
    return amount_received - amount_sent


def get_last_blockchain_value():
    """ Returns the last value of the current blockchain. """
    if len(blockchain) < 1:
        return None
    return blockchain[-1]


def add_transaction(recipient, amount=1.0, sender=owner):
    """ Appends a new value as well as the last blockchain to the blockchain.
        :argument sender The sender of the coins.
        :argument recipient The recipient of the coins.
        :argument amount The amount of coins (default[1])
    """
    transaction = Transaction(sender, recipient, amount)
    verifier = Verification()
    if verifier.verify_transaction(transaction, get_balance):
        open_transactions.append(transaction)
        save_data()
        return True
    return False


def mine_block():
    """ Mines a new block in the blockchain. """
    last_block = blockchain[-1]
    hashed_block = hash_util.hash_block(last_block)

    proof = proof_of_work()

    reward_transaction = Transaction('MINING', owner, MINING_REWARD)
    copied_transactions = open_transactions[:]  # Creates a new list with all the values from the original list.
    copied_transactions.append(reward_transaction)
    block = Block(len(blockchain), hashed_block, copied_transactions, proof)
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


waiting_for_input = True

while waiting_for_input:
    print('Please choose an option: ')
    print('1: Add a new transaction value')
    print('2: Mine a new block')
    print('3: Output the blockchain blocks')
    print('4: Check transactions validity')
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
            save_data()
    elif user_choice == '3':
        print_blockchain_elements()
    elif user_choice == '4':
        verifier = Verification()
        if verifier.verify_transactions(open_transactions, get_balance):
            print('All transactions are valid!')
        else:
            print('There are invalid transactions!')
    elif user_choice == '9':
        waiting_for_input = False
    else:
        print('Input was invalid, please, choose a value from the list!')

    # After each action, we verify if the chain was not manipulated
    verifier = Verification()
    if not verifier.verify_chain(blockchain):
        print('Invalid blockchain!')
        waiting_for_input = False
    print('Balance of {}: {:6.2f}'.format('Kelvin', get_balance('Kelvin')))
print('Done!')
