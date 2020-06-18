# Initializing our blockchain list
blockchain = []


def get_last_blockchain_value():
    """ Returns the last value of the current blockchain. """
    if len(blockchain) < 1:
        return None
    return blockchain[-1]


def add_value(transaction_amount, last_transaction):
    """ Appends a new value as well as the last blockchain to the blockchain.
        :argument transaction_amount The amount that should be added.
        :argument last_transaction The last blockchain transaction (default [1]).
    """
    if last_transaction is None:
        last_transaction = [1]
    blockchain.append([last_transaction, transaction_amount])


def get_transaction_value():
    """ Returns the input of the user (a new transaction amount) as a float. """
    return float(input('Your transaction amount, please: '))


def get_user_choice():
    return input('Your choice: ')


def print_blockchain_elements():
    print('-' * 20 + ' Printing elements ' + '-' * 20)
    for block in blockchain:
        print('Outputting Block')
        print(block)
    else:
        print('-' * 59)


def verify_chain():
    is_valid = True
    for block_index in range(len(blockchain)):
        if block_index == 0:
            continue
        elif blockchain[block_index][0] != blockchain[block_index - 1]:
            is_valid = False
            break
    return is_valid


waiting_for_input = True

while waiting_for_input:
    print('Please choose an option: ')
    print('1: Add a new transaction value')
    print('2: Output the blockchain blocks')
    print('3: Manipulate the blockchain')
    print('9: Quit')
    user_choice = get_user_choice()
    if user_choice == '1':
        tx_amount = get_transaction_value()
        add_value(last_transaction=get_last_blockchain_value(), transaction_amount=tx_amount)
    elif user_choice == '2':
        print_blockchain_elements()
    elif user_choice == '3':
        if len(blockchain) >= 1:
            blockchain[0] = 2
    elif user_choice == '9':
        waiting_for_input = False
    else:
        print('Input was invalid, please, choose a value from the list!')

    # After each action, we verify if the chain was not manipulated
    if not verify_chain():
        print('Invalid blockchain!')
        waiting_for_input = False

print('Done!')
