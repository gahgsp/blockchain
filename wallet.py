import binascii

import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


class Wallet:

    def __init__(self):
        self.private_key = None
        self.public_key = None

    def create_keys(self):
        """
        Creates a new pair of public and private keys.
        """
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def save_keys(self):
        """
        Saves the created keys into a file.
        """
        if self.public_key is not None and self.private_key is not None:
            try:
                with open('wallet.txt', mode='w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.public_key)
            except (IOError, IndexError):
                print('An error occurred while saving the wallet!')

    def load_keys(self):
        """
        Loads the keys from the file into memory.
        """
        try:
            with open('wallet.txt', mode='r') as f:
                keys = f.readlines()
                public_key = keys[0][:-1]  # Extracts the entire row without the last character that is the \n char.
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
        except (IOError, IndexError):
            print('An error occurred while loading the wallet!')

    def generate_keys(self):
        """
        Generates a new pair of public and private keys using a cryptography algorithm.
        :return:
        """
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
                binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii'))

    def sign_transaction(self, sender, recipient, amount):
        """
        Signs a transaction and returns its signature.
        :param sender: the sender of the transaction.
        :param recipient: the recipient of the transaction.
        :param amount: the amount of coins of the transaction.
        :return: the signature for the given transaction.
        """
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_transaction(transaction):
        """
        Verifies the signature of a given transaction.
        :param transaction: the transaction that should have its signature validated.
        :return: if the signature of the transaction is valid or not.
        """
        if transaction.sender == 'MINING':
            return True

        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))
