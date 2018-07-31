from Orses_Competitor_Core.Block_Data_Aggregator import GenesisBlock, GenesisBlockHeader
from Orses_Util_Core.FileAction import FileAction
from Orses_Cryptography_Core.Hasher import Hasher
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Crypto.Hash import SHA256
from collections import Iterable
from Orses_Util_Core.MerkleRootTree import OrsesMerkleRootTree


import multiprocessing, json

genesis_block = {
    "block_header": {
        "block_number": 0,
        "merkle_root":"456f4f16b6abbcd4ee4f06e0f96c511c8731ee8b77e68fe7ab25fc6e8171bfa2",
        "nonce": format(6401023, "x"),  # turns to hex without the 0X
        "extra_nonce": None,  # none if not used
        "primary_signatory": "Wb7a215ba22c92eff072f8f9c5923a24f89e9a47c",
        "extraNonce": 0,
        "block_hash": "fffffff77ccfa2d4a369782ea43d39fb30ac33066274504b01de7a0105a6b155",

    },

    "validity_protocol": "This will a set of rules that dictates what makes a block valid",

    "tats": {  # example, main net genesis block would possible have 100s to 1000s of Token Association Transaction
        "feaa53609b4265078f8cef123ba43e01cc2ca6871f05bea9efafa6133a9914c5": {
            "Wd8661c5e3c7b93f5344f4c2536470f383071dd43": 850_000_000.00
        },

        "c8472e1e64cfe50d6572691b8969a5f7e3ac8115aff39f36fe40b753a4af579a": {
            "W0df521b542a840cb5d5ed6c819e913af83b4baa4": 150_000_000.00
        },

        "ecbc97cd733a59c53e47779fe2952700693433b2ffe21292465e350f4173d68d": {
            "W82d9d7288822e181851add314956744f308d7841": 35_000_000.00
        },

        "f565b624af274d345b268fbe15c108064d0b10c2d4d17d6ad0bb8064e939bb8d": {
            "Waaa4adb908bd17966b757b8fe93d4f95330ff2c6": 50_000_000.00
        }
    },

    "genesis_BCW": {
        "This will have a list of Token reservation requests of initial Blockchain connected wallets"
    },

    "genesis_pub_key": "base85 encoded public key of private key of creator. Private key only used once and is RSA3072",

    "genesis_sig": "base85 string of signature by creator, can be used to validate correct genesis block",


    "gen_sec_signatories": {  # genesis secondary signatories
        "ffffff356938f71a8ce16181fac78c6785720b1fafbbdc21c055d074634d8865": {
            "W9d313a84e7d6e4191d4ff7b3aa50be43fe6ea8cb": 0.0
        }
    }

}

#
# def create_reward_transaction(reward_wallet, set_of_secondary_signatories_wallet):
#     """
#
#     :param reward_wallet:
#     :param list_of_secondary_signatories_wallet:
#     :return:
#     """
#
#     # todo: check whitepaper for proper reward mechanisim
#     reward_tx = {
#         "rwd_wid": reward_wallet,
#         "other_wid": set_of_secondary_signatories_wallet,
#         "prim_reward": 50,
#         "other_reward": 10
#     }
#
#     return {"rwd": reward_tx, "tx_hash": SHA256.new(json.dumps(reward_tx).encode()).hexdigest()}
#
#
# def compete_process(q_from_bk_propagator: multiprocessing.Queue,
#                     q_for_compete: multiprocessing.Queue,
#                     q_for_validator: multiprocessing.Queue, reward_wallet):
#     """
#     :param q_for_compete: queue from main process, data from propagator initiator is sent to before
#     :param reward_wallet: wallet to direct reward wallet.
#     :return:
#     """
#     # todo: Blockchain propagator should check
#
#     # BlockchainPropagator gets recent blocks from network and then sends the most recent block
#     recent_block = q_from_bk_propagator.get()  # [block_no, block]
#     forest = BlockForest(reward_wallet, blockNo=recent_block[0])
#
#     while True:
#
#         # receives main message dict
#         msg = q_for_compete.get()


class GenesisBlockCreator:

    def __init__(self):

        self.block = GenesisBlock()
        self.block_header_callable = GenesisBlockHeader
        self.tats = {
            "W3c8135240da9d25d3905aa7aca64c98ca6b1fede": 850_000_000,
            "W884c07be004ee2a8bc14fb89201bbc607e75258d": 425_000_000,
            "Wf2f140a956cec5cd6a1a6f7763378b239a007ac0": 425_500_000,
            "Wc8f7cc3576244c915e50e4410b988dfb6946f036": 150_000_000,
            "Wfa1f6617995833b679e090f88f90603cc9fbd485": 250_000_000,
            "W588cb886522c9861aa6cee60d4758e6fd4009cc1": 200_000_000,
            "Wb70877ab85be7e61eabbd2891811f5e42403611a": 200_000_000

        }

        self.merkle_root = self.compute_merkle_root()  # self.tats becomes {hash_of_tat: tat dict}
        self.dict_of_bcw = {
            "W3c8135240da9d25d3905aa7aca64c98ca6b1fede": 800_000,
            "W884c07be004ee2a8bc14fb89201bbc607e75258d": 250_000
        }

    def set_before_competing(self):
        self.block.set_before_compete(
            hash_of_protocol=self.get_validity_protocol(),
            tats=self.tats,
            dict_of_bcws=self.dict_of_bcw,
            pubkey_dict={
                "x": "on+no;S+oQ9XJ4o_+iJI+Ezi)ld5>}%>`YyAr?sc",
                "y": "f-_gqvfMWUx1j@JDUVQ@EbNV&H$a<Ha!y&&qg3w?"
            },
            # signature=DigitalSigner.sign_with_provided_privkey(
            #     dict_of_privkey_numbers={
            #         'x': 60785994004755780541968889462742035955235637618029604119657448498380482761088,
            #         'y': 100309319245511545150569175878829989424599308092677960010907323326738383429364,
            #         'd': 29950300400169917180358605208938775880760212514399944926857005417377480590100
            #     },
            #     message=json.dumps(self.tats).encode()
            # )

        )

    def set_after_competing(self):
        """
        after compete, create a GenesisBlockHeader instance, set the necessary attributes
        :return:
        """
        pass

    def compute_merkle_root(self):
        list_of_tat_hashes = list()
        tat_with_hash = dict()

        for tat in self.tats:
            data = json.dumps(tat).encode()
            hash_id = Hasher.sha_hasher(data=data)
            list_of_tat_hashes.append(hash_id)
            tat_with_hash[hash_id] = {tat: self.tats[tat]}

        self.tats = tat_with_hash

        if list_of_tat_hashes:
            o = OrsesMerkleRootTree(items=sorted(list_of_tat_hashes))
            o.create_merkle_tree()
            return o.get_merkle_root()

    @staticmethod
    def get_validity_protocol():
        data = FileAction.open_file_into_byte("Validity_Protocol", in_folder="Orses_Competitor_Core")

        return Hasher.sha_hasher(data=data, hash_form="b85_str")


if __name__ == '__main__':
    gen_block = GenesisBlockCreator()
    gen_block.set_before_competing()
    print(gen_block.block.__dict__)