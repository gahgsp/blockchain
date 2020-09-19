from blockchain import Blockchain

from verification import Verification


class Node:

    def __init__(self):
        # self.id = str(uuid4())
        self.id = 'Kelvin'
        self.blockchain = Blockchain(self.id)

    def get_transaction_value(self):
        """ Returns the input of the user (a new transaction amount) as a float. """
        tx_recipient = input('Enter the recipient of the transaction:')
        tx_amount = float(input('Your transaction amount, please:'))
        return tx_recipient, tx_amount

    def get_user_choice(self):
        """ Returns the input from the user. """
        return input('Your choice: ')

    def print_blockchain_elements(self):
        """ Print all the blockchain elements. """
        print('-' * 20 + ' Printing elements ' + '-' * 20)
        for block in self.blockchain.chain:
            print('Outputting Block')
            print(block)
        else:
            print('-' * 59)

    def listen_for_input(self):
        waiting_for_input = True

        while waiting_for_input:
            print('Please choose an option: ')
            print('1: Add a new transaction value')
            print('2: Mine a new block')
            print('3: Output the blockchain blocks')
            print('4: Check transactions validity')
            print('9: Quit')
            user_choice = self.get_user_choice()
            if user_choice == '1':
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data
                if self.blockchain.add_transaction(recipient, amount, self.id):
                    print('Transaction has been added successfully!')
                else:
                    print('The transaction has failed!')
                print(self.blockchain.open_transactions)
            elif user_choice == '2':
                self.blockchain.mine_block()
            elif user_choice == '3':
                self.print_blockchain_elements()
            elif user_choice == '4':
                verifier = Verification()
                if verifier.verify_transactions(self.blockchain.open_transactions, self.blockchain.get_balance):
                    print('All transactions are valid!')
                else:
                    print('There are invalid transactions!')
            elif user_choice == '9':
                waiting_for_input = False
            else:
                print('Input was invalid, please, choose a value from the list!')

            # After each action, we verify if the chain was not manipulated
            verifier = Verification()
            if not verifier.verify_chain(self.blockchain.chain):
                print('Invalid blockchain!')
                waiting_for_input = False
            print('Balance of {}: {:6.2f}'.format(self.id, self.blockchain.get_balance()))
        print('Done!')


node = Node()
node.listen_for_input()
