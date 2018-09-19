"""
This class holds all the transactions/messages waiting to be included in block.
It also cfeates and manages files needed to verify a wallet's token balance

It also includes transaction/messages already in block (last 10 blocks)
"""

import json
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData


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

    def update_mempool(self, winning_block: dict) -> bool:
        """
        Use this to update mempool.
        this includes moving transactions in unconfirmed to confirmed that have been included in the last block
        updating block number and pruning
        :param winning_block:
        :return:
        """
        try:
            block_activities = winning_block["block_activity"]
            db_manager = self.admin_inst.get_db_manager()
        except KeyError:
            # specifically for block 0 no key called "block activity" in genesis block
            pass
        else:
            for active_list in block_activities:
                # hash of activity is always index 0 (first element)
                # will move to confirmed, if hash is not in confirmed will do nothing
                self.move_from_unconfirmed_to_confirmed(msg_hash=active_list[0], db_manager=db_manager)

        self.update_next_block_no(new_block_no=int(winning_block["bh"]["block_no"])+1, new_block=winning_block)

        return True

    def update_next_block_no(self, new_block_no: int, new_block: dict) -> None:
        self.next_block_no = new_block_no
        block_no_mempool_data_to_delete = new_block_no - self.blocks_before_delete
        if block_no_mempool_data_to_delete in self.valid_msg_with_preview_hash:
            del self.valid_msg_with_preview_hash[block_no_mempool_data_to_delete]
        if block_no_mempool_data_to_delete in self.invalid_msg_with_preview_hash:
            del self.invalid_msg_with_preview_hash[block_no_mempool_data_to_delete]

        self.valid_msg_with_preview_hash[self.next_block_no] = dict()
        self.invalid_msg_with_preview_hash[self.next_block_no] = dict()

        # start a process that updates wallet balance
        if new_block_no > 1:  # means old block is at least block 1

            # todo: run in another thread
            self.update_wallet_balances_bcw_db(new_block=new_block)

    def update_wallet_balances_bcw_db(self, new_block):
        """
        This updates the permanent wallet balances db;

        It also adds
        :param new_block:
        :return:
        """

        # todo: refactor
        block_activities = new_block["block_activity"]
        db_manager = self.admin_inst.get_db_manager()

        # todo: instantiate leveldb of unconfirmed and unconfirmed_wid, and update balance according to wid

        # loop through each tx hash in block activity, check if it is in unconfirmed dict,
        # add or subtract balances as need. if a reservation request is found, add to bcw.
        # Make sure any tx added to blockchain is deleted from unconfirmed



    def load_helper_files(self):
        """

        :return:
        """

    def update_helper_files(self):
        """
        several files
        :return:
        """

    def insert_valid_into_unconfirmed(self, msg_hash: str, msg):
        """
        insert transaction into valid block
        :param msg:
        :return:
        """

    def move_from_unconfirmed_to_confirmed(self, msg_hash: str, db_manager):
        """
        insert into confirmed leveldb
        if msg_hash is not in unconfirmed will do nothing
        :return:
        """


        # print(f"in Mempool: confirmed dict {self.confirmed},  hash is {msg_hash}, unconfirmed is {self.uncomfirmed}")

        # pop tx from unconfirmed
        tx_list = db_manager.get_from_unconfirmed_db(
            tx_hash=msg_hash,
            pop_value=True,
            json_decoded=False
        )

        # if tx is not empty then insert tx into confirmed
        if tx_list:
            db_manager.insert_into_confirmed_db(
                tx_hash=msg_hash,
                tx_list=tx_list
            )
            tx_list = json.loads(tx_list)

            # todo: update permanent wallet balance
            snd_wid = tx_list[-1]
            rcv_wid = tx_list[-2]

    def insert_into_valid_msg_preview_hash(self, hash_prev, msg):
        """
        insert valid msg preview
        :param hash_prev:
        :param msg:
        :return:
        """
        try:
            self.valid_msg_with_preview_hash[self.next_block_no][hash_prev] = msg
            print(f"in Mempool, msg in valid_msg_prev: {msg}")
            # try:
            #     msg_hash = msg["tx_hash"]
            # except KeyError:
            #     msg_hash = msg["msg_hash"]

        except KeyError:
            print(f"Error, tried to insert using new block number, but has not been blockNo: {self.next_block_no}")
            return False
        else:
            # self.uncomfirmed[msg_hash] = msg

            return True

    def check_valid_msg_hash_prev_dict(self, hash_prev):

        # will loop from current_block_no to current_block_no minus number of blocks hash prev is kep

        print(f"mempool debuging\n"
              f"next_block_no {self.next_block_no}\n"
              f"blocks_before_delete {self.blocks_before_delete}\n"
              f"valid_msg_with_preview_hash {self.valid_msg_with_preview_hash}\n"
              f"admin {self.admin_inst.admin_name}\n\n")

        if self.next_block_no is None:
            # load current known l
            self.next_block_no = BlockChainData.get_current_known_block(admin_instance=self.admin_inst)[0]+1

        for block_no_index in range(self.next_block_no, self.next_block_no - self.blocks_before_delete, -1):
            try:
                if hash_prev in self.valid_msg_with_preview_hash[block_no_index]:
                    return True
            except KeyError:
                print(f"in Mempool check valid, key not in dict key: {block_no_index}")
                pass

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

        if self.next_block_no is None:
            # load current known l
            self.next_block_no = BlockChainData.get_current_known_block(admin_instance=self.admin_inst)[0]+1
        # will loop from current_block_no to current_block_no minus number of blocks hash prev is kep
        for block_no_index in range(self.next_block_no, self.next_block_no - self.blocks_before_delete, -1):
            try:
                if hash_prev in self.invalid_msg_with_preview_hash[block_no_index]:
                    return True
            except KeyError:
                print(f"in Mempool.py check invalid, key not in dict key: {block_no_index}")
                pass

        return False




