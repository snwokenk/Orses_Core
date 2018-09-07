"""

module used to validate new blocks,
validation requires:
block is gotten from WinnerValidator, which validates the winning hash and receives the
winning block(and the other runner ups)

rules for block validation:

1.) probability of block hash is not greater than the maximum probability specified in the block previous 2nd block. ie.
    if current blockNo is 10 then blockNo 9's maximum probability is used

2.) block primary char and shuffled also determined by the previous 2nd block


3. verify that wallets sending tokens through transfer transactions have enough balance to

4. verify the net flow of each Blockchain connected wallet hash state. each block contains hash states of
    blockchain_connected wallets and along with this hash state a net inflow dictionary is given.
    The net inflow of a bk_connected wallet is calculated by:
    a) finding tokens transferred within a  the bk_conn wallet in which inputs of tokens are from assignment statements
        within another bk_conn wallet (+)
    b.) finding tokens transferred within another bk_conn wallet in which input of tokens are from assignment statements
        within the current bk_conn wallet (-)
    c) The net inflow is adding the transactions of a and subtracting the transactions of b

    ie bk_conn wallet A and bk_conn wallet B, transfer_tx "fabb"
    hash_state = {
        'wallet_state': "fabc349cd",  # hash state
        "merkle_root_asg_stmt": "fabb4sf", # merkle root of assignment statements
        "merkle_root_proof_tx": "abc123f", # merkle root of proof tx ( tx giving/receovomg all inputs of regular wallet
                                             from one bk_connected wallet to another
        "start_bal": 250000.0,
        "beg_accum_fees": 0.0,
        "net_inflow": {
            "B": -100.0,
            "tx_fabb": 120.012,
        },
        "end_accum_fees": 0.012,
        "end_bal": 250020,
        "assg_stmt_token_value": 120.00

    }

5.) it is not required to validate each individual bk_conn wallet's transactions

"""
from Orses_Validator_Core.BaseBlockValidator import BaseBlockValidator
from Orses_Util_Core.MerkleRootTree import OrsesMerkleRootTree
from Orses_Util_Core.Inherited_Classes import BlockChainDataInherited, CompetitorInherited, \
    competitive_hasher_func, get_qualified_hashes_func


# todo: once block is valid, send it off to WinnerValidator, This Process Validates blocks and then sends the winning
# todo: block to other blockpropagator, compete process
class NewBlockValidator(BaseBlockValidator):
    """
    A Base Class
    """
    def __init__(self, block, admin_inst, block_propagator_inst,  is_newly_created=False, q_object=None):
        super().__init__(
            block=block,
            admin_inst=admin_inst,
            is_newly_created=is_newly_created,
            q_object=q_object
        )
        self.block_header = self.block["bh"]
        self.block_propagator_inst = block_propagator_inst

    def validate(self):

        if self.verify_merkle_root_parts() and self.verify_block_hash_meets_target() and \
                self.verify_random_bytes_included():
            print("Block Validated by Validator")

            # this q object is connected to run_block_winner_chooser_process() method of BlockchainPropagator class
            # send validated block
            if self.q_object:
                self.q_object.put(self.block)
            return True
        else:
            print(f"Block NOT Validated by Validator, block:\n{self.block}")
            return False

    def validate_reward_txs(self):
        pass

    def validate_ttx(self):
        pass

    def validate_rsv_req(self):
        pass

    def validate_rvk_req(self):
        pass

    def validate_wsh(self):
        pass

    def verify_merkle_root_parts(self):
        block_actvity = self.block["block_activity"]
        list_for_merkle_root = [item[0] for item in block_actvity]
        o = OrsesMerkleRootTree(list_for_merkle_root)
        o.create_merkle_tree()

        merkle_root_validated = o.merkle_root == self.block_header["mrh"]


        print(f" is merkle root validated {merkle_root_validated}")
        print(f"merkle root from block {self.block_header['mrh']}\n"
              f"merkle root recreated {o.merkle_root}")

        return merkle_root_validated

    def verify_random_bytes_included(self):
        """
        this will check that the 5 random bytes are included from
        :return:
        """
        # todo: add the logic verifying random bytes are in block and proxy nodes providing these random bytes did
        # todo: not provide for the last two blocks
        return True

    def verify_block_hash_meets_target(self) -> bool:
        """
        verify that hash of block meets required probability target
        :return:
        """

        previous_block_no = self.prev_blockNo

        c = CompetitorInherited(
            reward_wallet="0",
            admin_inst=self.admin_inst,
            just_launched=False if previous_block_no > 0 else False
        )

        if previous_block_no > 0:
            start_time, len_of_competition, single_prime_char, exp_leading_prime, new_block_no, addl_chars, \
                prev_hash = c.get_new_block_arguments(rsp=self.block)
        elif previous_block_no == 0:
            start_time, len_of_competition, single_prime_char, exp_leading_prime, new_block_no, addl_chars, \
                prev_hash = c.get_block_one_arguments()
        else:
            print("block hash is False")
            return False

        try:
            merkle_root = self.block_header["mrh"]
            extra_nonce = self.block_header["x_n"]

            # turn nonce back to int from hex str
            nonce = int(self.block_header["n"], 16)

            combined_merkle = f'{extra_nonce}{merkle_root}{prev_hash}'
            is_hash_valid = get_qualified_hashes_func(
                prime_char=single_prime_char*exp_leading_prime,
                extra_nonce=None,
                nonce=None,
                hash_hex=competitive_hasher_func(f'{combined_merkle}{nonce}{prev_hash}'.encode()),
                len_prime_char=exp_leading_prime,
                check_if_valid=True

            )
            print("In NewBlockValidator  Hash Is Valid", is_hash_valid)
        except Exception as e:
            print(f"in New Block Validator exception {e}")
            return False
        else:
            return is_hash_valid

    def validate_block_activities(self):
        """
        use this method to validate activities in "block_activity" section
        :return:
        """

        # todo: check mempool if hash in valid uncomfirmed, if it is not, check to make sure hash IS NOT in comfirmed
        # todo: (last 20 blocks). If it is not, pass the message into validators

        # for activity in self.block["block_activity"]:
        #
        #     # activity = [hash, main_msg list or dict
        #     # check if hash in validated transactions
        #     if activity[0] in self.block_propagator_inst.

    def get_block(self, block_no):

        return BlockChainDataInherited.get_block(
            admin_instance=self.admin_inst,
            block_no=block_no
        )





if __name__ == '__main__':
    pass