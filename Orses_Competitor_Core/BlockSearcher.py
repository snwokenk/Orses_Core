"""
Used to search blocks for a transfer transaction hash, wallet state or misc messages
"""


class BlockChainSearch:
    """
    Use this class to search the blockchain and blocks
    """

    def __init__(self, admin_inst):

        self.admin_inst = admin_inst

    def is_hash_in_block(self, a_hash: str, block_no: int, get_activity: bool):
        """
        used to check if hash is block
        :param a_hash: a hash to check (SHA256)
        :param block_no: if provided, the block the hash should be in
        :param get_activity: if true, then full activity is
        :return: bool or full active, true or false  OR the activity related to hash
        """

    def search_hash_in_blockchain(self, a_hash: str, get_activity: bool, block_no=None):
        """
        use this to search for a hash in the blockchain
        :param a_hash: SHA 256 hash
        :param get_activity: bool if to return full activity
        :param block_no: block hash should be in
        :return: bool or full detail
        """

    def get_wallet_hash_state(self, wallet_id: str):
        """
        used to get the wallet hash state, including the
        :param wallet_id: wallet id
        :return:
        """

    def get_wallet_balance(self, wallet_id):
        """
        used to get the balance of a wallet
        :param wallet_id:
        :return:
        """