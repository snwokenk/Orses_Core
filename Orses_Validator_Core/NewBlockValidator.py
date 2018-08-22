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


class NewBlockValidator(BaseBlockValidator):
    """
    A Base Class
    """
    def __init__(self, block_no, block, admin_inst, is_newly_created=False, q_object=None):
        super().__init__(
            block_no=block_no,
            block=block,
            admin_inst=admin_inst,
            is_newly_created=is_newly_created,
            q_object=q_object
        )

    def validate(self):

        return True  # for now just return true

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




if __name__ == '__main__':
    pass