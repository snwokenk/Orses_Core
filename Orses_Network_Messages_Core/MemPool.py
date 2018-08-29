"""
This class holds all the transactions/messages waiting to be included in block.

It also includes transaction/messages already in block (last 10 blocks)
"""


class MemPool:

    def __init__(self):
        self.uncomfirmed = dict()
        self.confirmed = dict()
        self.valid_msg_with_preview_hash = dict()

    def insert_valid_into_unconfirmed(self, msg):
        """
        insert transaction into valid block
        :param msg:
        :return:
        """
        pass

    def insert_into_confirmed(self):
        """
        insert into confirmed
        :return:
        """

    def insert_into_valid_msg_preview_hash(self, hash_prev, msg):
        """
        insert valid msg preview
        :param hash_prev:
        :param msg:
        :return:
        """

