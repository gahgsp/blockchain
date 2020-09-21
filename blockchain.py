import json
from functools import reduce

import requests

from block import Block
from transaction import Transaction
from utils import hash_util
from utils.verification import Verification
from wallet import Wallet

MINING_REWARD = 10


class Blockchain:

    def __init__(self, hosting_node_id, node_id):
        # Starting block for the blockchain.
        genesis_block = Block(0, '', [], 100, 0)
        # Initializing our blockchain list.
        self.__chain = [genesis_block]
        # Unhandled transactions.
        self.__open_transactions = []
        self.hosting_node = hosting_node_id
        self.node_id = node_id
        self.__peer_nodes = set()
        self.resolve_conflicts = False
        # Loads the data of the blockchain from a save file.
        self.load_data()

    def get_chain(self):
        return self.__chain[:]  # Returns a copy reference of the blockchain.

    def get_open_transactions(self):
        return self.__open_transactions[:]  # Returns a copy reference of the open transactions list.

    def load_data(self):
        """
        Loads the the blockchain and open transactions from save file.
        """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    converted_transaction = [Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature'])
                                             for tx in
                                             block['transactions']]
                    updated_block = Block(block['index'],
                                          block['previous_hash'],
                                          converted_transaction,
                                          block['proof'],
                                          block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])
                updated_transactions = []
                for transaction in open_transactions:
                    updated_transaction = Transaction(transaction['sender'], transaction['recipient'],
                                                      transaction['amount'], transaction['signature'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions

                # Loading the peer nodes from the file.
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except IOError:
            print('File not found! Initializing the Blockchain with default values...')

    def save_data(self):
        """
        Saves the current state of the blockchain plus its open transactions to a file.
        """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                saveable_chain = [block.__dict__ for block in [
                    Block(bl.index, bl.previous_hash, [tx.__dict__ for tx in bl.transactions], bl.proof, bl.timestamp)
                    for
                    bl in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_transactions = [transaction.__dict__ for transaction in self.__open_transactions]
                f.write(json.dumps(saveable_transactions))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
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

    def get_balance(self, sender=None):
        """
        Calculates the current balance for a participant.
        :return: the total balance of the participant.
        """
        if sender is None:
            if self.hosting_node is None:
                return None
            participant = self.hosting_node
        else:
            participant = sender
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

    def add_transaction(self, recipient, amount=1.0, sender=None, signature='', is_receiving=False):
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
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast'.format(node)
                    try:
                        response = requests.post(url, json={'sender': sender, 'recipient': recipient, 'amount': amount,
                                                            'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined!')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
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
        for node in self.__peer_nodes:
            url = 'http://{}/broadcastBlock'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Mining declined!')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        """
        Add an already created Block when broadcasting Blocks from different peers.
        :param block: the Block that will be added.
        :return: if the addition was successfully.
        """
        transactions = [
            Transaction(
                transaction['sender'],
                transaction['recipient'],
                transaction['amount'],
                transaction['signature']) for transaction in block['transactions']
        ]
        proof_is_valid = Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_util.hash_block(self.get_chain()[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(block['index'], block['previous_hash'], transactions, block['proof'],
                                block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        for incoming_transaction in block['transactions']:
            for open_transaction in stored_transactions:
                if open_transaction.sender == incoming_transaction['sender'] \
                        and open_transaction.recipient == incoming_transaction['recipient'] \
                        and open_transaction.amount == incoming_transaction['amount'] \
                        and open_transaction.signature == incoming_transaction['signature']:
                    try:
                        self.__open_transactions.remove(open_transaction)
                    except ValueError:
                        print('The transaction was already removed!')
        self.save_data()
        return True

    def resolve(self):
        """
        Resolves the chain conflicts using a Consensus Algorithm.
        :return: if the chain was replaced or kept the local chain.
        """
        winner_chain = self.get_chain()
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [
                    Block(
                        block['index'],
                        block['previous_hash'],
                        [Transaction(
                            transaction['sender'],
                            transaction['recipient'],
                            transaction['amount'],
                            transaction['signature']) for transaction in block['transactions']],
                        block['proof'],
                        block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.__chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        """
        Adds a new node to the peer nodes set.
        :param node: the node URL which will be added to the set.
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """
        Removes a node from the peer nodes set.
        :param node: the node URL which will be removed from the set.
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """
        Returns a list of all the current peer nodes in the blockchain.
        :return: a list containing all the nodes in the blockchain.
        """
        return list(self.__peer_nodes)
