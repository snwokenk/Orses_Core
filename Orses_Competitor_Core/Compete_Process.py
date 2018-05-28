from .Block_Data_Aggregator import BlockAggregator
from Orses_Util_Core.BinarySearchTree import BlockForest
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData
import multiprocessing, json
from Crypto.Hash import SHA256

genesis_block = {
    "block_header": {
        "protocol_rule_hash": "fe3f01abad",
        "merkle_root":"d88397fb3c91614409bf6358848baa305aea28bbc2cc1ba87503ca2f20cfb578",
        "nonce:": format(41042163, "x"),  # turns to hex without the 0X
        "extraNonce": 0,
        "block_hash": "000000a75ea76fbe7af548c521c8275d005229363300da297f2f022814928814",
        "block_number": 0
    },
    "tka": {
        "Wd8661c5e3c7b93f5344f4c2536470f383071dd43": 850_000_000,
        "W0df521b542a840cb5d5ed6c819e913af83b4baa4": 150_000_000,
        "W82d9d7288822e181851add314956744f308d7841": 35_000_000,
        "Waaa4adb908bd17966b757b8fe93d4f95330ff2c6": 50_000_000
    },

}


def create_reward_transaction(reward_wallet, set_of_secondary_signatories_wallet):
    """

    :param reward_wallet:
    :param list_of_secondary_signatories_wallet:
    :return:
    """

    # todo: check whitepaper for proper reward mechanisim
    reward_tx = {
        "rwd_wid": reward_wallet,
        "other_wid": set_of_secondary_signatories_wallet,
        "prim_reward": 50,
        "other_reward": 10
    }

    return {"rwd": reward_tx, "tx_hash": SHA256.new(json.dumps(reward_tx).encode()).hexdigest()}


def compete_process(q_from_bk_propagator: multiprocessing.Queue,
                    q_for_compete: multiprocessing.Queue,
                    q_for_validator: multiprocessing.Queue, reward_wallet):
    """
    :param q_for_compete: queue from main process, data from propagator initiator is sent to before
    :param reward_wallet: wallet to direct reward wallet.
    :return:
    """
    # todo: Blockchain propagator should check

    # BlockchainPropagator gets recent blocks from network and then sends the most recent block
    recent_block = q_from_bk_propagator.get()  # [block_no, block]
    forest = BlockForest(reward_wallet, blockNo=recent_block[0])

    while True:

        # receives main message dict
        msg = q_for_compete.get()


if __name__ == '__main__':
    pass