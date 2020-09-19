import hash_util


class Verification:

    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        """
        Validates a proof of work number to check if it is valid to solve the hash algorithm.
        :param transactions: the transactions of the block for whick the proof is validated.
        :param last_hash: the previous block hash which will be store in the current guess for the hash.
        :param proof: the proof number we are testing.
        :return: if the generated hash is a valid hash based on the given condition.
        """
        # Creates a String containing all the hash inputs.
        guess = (str([transaction.to_ordered_dict() for transaction in transactions]) + str(last_hash) + str(
            proof)).encode()
        # Hashes the String.
        guess_hash = hash_util.hash_string_256(guess)
        # Only a hash based on the above inputs that starts with two 0s is valid for the algorithm.
        # This condition can be changed, but once adding more characters to validate, the more time consuming it is.
        return guess_hash[0:2] == '00'

    @classmethod
    def verify_chain(cls, blockchain):
        """ Verifies if the blockchain was not manipulated. """
        # When enumerating a list, it returns a pair of index and value (tuple)
        for (index, block) in enumerate(blockchain):
            if index == 0:  # Genesis block
                continue
            if block.previous_hash != hash_util.hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print("Proof of Work is invalid!")
                return False
        return True

    @staticmethod
    def verify_transaction(transaction, get_balance):
        """
        Verify if a transaction is possible based on the amount of coins of a given sender.
        :param transaction: the transaction that should be verified.
        :return: if the transaction is possible or not.
        """
        sender_balance = get_balance()
        return sender_balance >= transaction.amount

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        """
        Verifies all open transactions.
        :return: if all the open transactions are valid transactions.
        """
        return all([cls.verify_transaction(tx, get_balance) for tx in open_transactions])
