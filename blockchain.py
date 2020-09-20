import json
from functools import reduce

from block import Block
from transaction import Transaction
from utils import hash_util
from utils.verification import Verification
from wallet import Wallet

MINING_REWARD = 10


class Blockchain:

    def __init__(self, hosting_node_id):
        # Starting block for the blockchain.
        genesis_block = Block(0, '', [], 100, 0)
        # Initializing our blockchain list.
        self.__chain = [genesis_block]
        # Unhandled transactions.
        self.__open_transactions = []
        # Loads the data of the blockchain from a save file.
        self.load_data()
        self.hosting_node = hosting_node_id

    def get_chain(self):
        return self.__chain[:]  # Returns a copy reference of the blockchain.

    def get_open_transactions(self):
        return self.__open_transactions[:]  # Returns a copy reference of the open transactions list.

    def load_data(self):
        """
        Loads the the blockchain and open transactions from save file.
        """
        try:
            with open('blockchain.txt', mode='r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    converted_transaction = [Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature']) for tx in
                                             block['transactions']]
                    updated_block = Block(block['index'],
                                          block['previous_hash'],
                                          converted_transaction,
                                          block['proof'],
                                          block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain
                open_transactions = json.loads(file_content[1])
                updated_transactions = []
                for transaction in open_transactions:
                    updated_transaction = Transaction(transaction['sender'], transaction['recipient'],
                                                      transaction['amount'], transaction['signature'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
        except IOError:
            print('File not found! Initializing the Blockchain with default values...')

    def save_data(self):
        """
        Saves the current state of the blockchain plus its open transactions to a file.
        """
        try:
            with open('blockchain.txt', mode='w') as f:
                saveable_chain = [block.__dict__ for block in [
                    Block(bl.index, bl.previous_hash, [tx.__dict__ for tx in bl.transactions], bl.proof, bl.timestamp)
                    for
                    bl in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_transactions = [transaction.__dict__ for transaction in self.__open_transactions]
                f.write(json.dumps(saveable_transactions))
        except IOError:
            print('Saving failed!')

    def proof_of_work(self):
        """
        Generates a proof of work for the open transactions, based on the last hashed block which is guessed until it fits.
        :return: a valid number for the proof of work.
        """
        last_block = self.__chain[-1]
        last_hash = hash_util.hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self):
        """
        Calculates the current balance for a participant.
        :return: the total balance of the participant.
        """
        if self.hosting_node is None:
            return None

        participant = self.hosting_node
        # Fetches all the sent coins for the given person.
        # This fetches the sent amounts of transactions that were already included in the blockchain.
        tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participant] for block in self.__chain]
        # This fetches the sent amounts of open transactions (to avoid double spending).
        open_tx_sender = [tx.amount for tx in self.__open_transactions if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender,
                             0)

        # Fetches all the received coins for the given person.
        # This does not consider open transactions because we can not spend the coins
        # before the transactions was confirmed and add to the blockchain.
        tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participant] for block in
                        self.__chain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0,
                                 tx_recipient, 0)

        # Calculates and return the balance.
        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        """ Returns the last value of the current blockchain. """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(self, recipient, amount=1.0, sender=None, signature=''):
        """ Appends a new value as well as the last blockchain to the blockchain.
            :argument sender The sender of the coins.
            :argument recipient The recipient of the coins.
            :argument amount The amount of coins (default[1])
        """
        if self.hosting_node is None:
            return False

        transaction = Transaction(sender, recipient, amount, signature)

        if not Wallet.verify_transaction(transaction):
            return False

        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            return True
        return False

    def mine_block(self):
        """ Mines a new block in the blockchain. """
        if self.hosting_node is None:
            return None

        last_block = self.__chain[-1]
        hashed_block = hash_util.hash_block(last_block)

        proof = self.proof_of_work()

        reward_transaction = Transaction('MINING', self.hosting_node, MINING_REWARD, '')
        copied_transactions = self.__open_transactions[
                              :]  # Creates a new list with all the values from the original list.
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block, copied_transactions, proof)

        for transaction in block.transactions:
            if not Wallet.verify_transaction(transaction):
                return None

        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        return block
