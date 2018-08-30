"""
This class holds all the transactions/messages waiting to be included in block.

It also includes transaction/messages already in block (last 10 blocks)
"""

import gc

class MemPool:

    def __init__(self, admin_inst, blocks_before_delete=20):
        self.admin_inst = admin_inst

        # number of blocks to keep certain data
        self.blocks_before_delete = blocks_before_delete

        self.uncomfirmed = dict()
        self.confirmed = dict()
        self.valid_msg_with_preview_hash = dict()
        self.invalid_msg_with_preview_hash = dict()

        self.valid_assignment_stmt_with_preview_hash = dict()
        self.invalid_assignment_stmt_with_preview_hash = dict()

        self.next_block_no = None

    def update_next_block_no(self, new_block_no):
        self.next_block_no = new_block_no
        block_no_mempool_data_to_delete = new_block_no - self.blocks_before_delete
        if block_no_mempool_data_to_delete in self.valid_msg_with_preview_hash:
            del self.valid_msg_with_preview_hash[block_no_mempool_data_to_delete]
        if block_no_mempool_data_to_delete in self.invalid_msg_with_preview_hash:
            del self.valid_msg_with_preview_hash[block_no_mempool_data_to_delete]

        self.valid_msg_with_preview_hash[new_block_no] = dict()
        self.invalid_msg_with_preview_hash[new_block_no] = dict()

    def insert_valid_into_unconfirmed(self, msg_hash, msg):
        """
        insert transaction into valid block
        :param msg:
        :return:
        """

    def insert_into_confirmed(self, msg_hash, msg):
        """
        insert into confirmed
        :return:
        """

        self.confirmed[msg_hash] = self.uncomfirmed[msg_hash]
        del self.uncomfirmed[msg_hash]

    def insert_into_valid_msg_preview_hash(self, hash_prev, msg):
        """
        insert valid msg preview
        :param hash_prev:
        :param msg:
        :return:
        """
        try:
            self.valid_msg_with_preview_hash[self.next_block_no][hash_prev] = msg
        except KeyError:
            print(f"Error, tried to insert using new block number, but has not been blockNo: {self.next_block_no}")
            return False

        return True

    def check_valid_msg_hash_prev_dict(self, hash_prev):

        # will loop from current_block_no to current_block_no minus number of blocks hash prev is kep
        for block_no_index in range(self.next_block_no, self.next_block_no - self.blocks_before_delete, -1):
            if hash_prev in self.valid_msg_with_preview_hash[block_no_index]:
                return True

        return False

    def insert_into_invalid_msg_preview_hash(self, hash_prev, msg):
        """
        insert into invalid dict
        :param hash_prev:
        :param msg:
        :return:
        """
        try:
            self.invalid_msg_with_preview_hash[self.next_block_no][hash_prev] = msg
        except KeyError:
            print(f"Error, tried to insert using new block number, but has not been blockNo: {self.next_block_no}")
            return False

        return True

    def check_invalid_msg_hash_prev_dict(self, hash_prev):

        # will loop from current_block_no to current_block_no minus number of blocks hash prev is kep
        for block_no_index in range(self.next_block_no, self.next_block_no - self.blocks_before_delete, -1):
            if hash_prev in self.invalid_msg_with_preview_hash[block_no_index]:
                return True

        return False




