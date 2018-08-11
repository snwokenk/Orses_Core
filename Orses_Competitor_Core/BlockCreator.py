from Orses_Competitor_Core.Block_Data_Aggregator import GenesisBlock, GenesisBlockHeader, BlockOne, BlockOneHeader
from Orses_Util_Core.FileAction import FileAction
from Orses_Cryptography_Core.Hasher import Hasher
from Crypto.Hash import SHA256
from collections import Iterable
from Orses_Util_Core.MerkleRootTree import OrsesMerkleRootTree


import json


class BaseBlockCreator:

    def __init__(self, primary_sig_wallet_id):
        self.block = None
        self.block_header_callable = None
        self.merkle_root = None
        self.primary_sig_wallet_id = primary_sig_wallet_id

    def get_block(self):
        return self.block

    def compute_merkle(self):
        pass  # override


class NonGenesisBlockCreator(BaseBlockCreator):

    def __init__(self, primary_sig_wallet_id):
        super().__init__(primary_sig_wallet_id=primary_sig_wallet_id)
        self.tx = dict()
        self.misc_msgs = dict()

    def compute_merkle(self):
        pass  # Override


class BlockOneCreator(NonGenesisBlockCreator):
    def __init__(self, primary_sig_wallet_id):
        super().__init__(primary_sig_wallet_id)
        self.block = BlockOne()
        self.block_header_callable = BlockOneHeader

    def set_before_competing(self, misc_msgs, transaction_dict):
        self.block.set_before_competing(
            misc_msgs=misc_msgs,
            transaction_dict=transaction_dict
        )


class GenesisBlockCreator:

    def __init__(self, primary_sig_wallet_id):
        self.primary_sig_wallet_id = primary_sig_wallet_id
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

        self.dict_of_bcw = {
            "W3c8135240da9d25d3905aa7aca64c98ca6b1fede": 800_000,
            "W884c07be004ee2a8bc14fb89201bbc607e75258d": 250_000
        }

        self.pubkey = {
            "x": "on+no;S+oQ9XJ4o_+iJI+Ezi)ld5>}%>`YyAr?sc",
            "y": "f-_gqvfMWUx1j@JDUVQ@EbNV&H$a<Ha!y&&qg3w?"
        }

        # self.tats becomes {hash_of_tat: tat dict}
        # *** should be last entry in __init__
        self.merkle_root = self.compute_merkle_root()

    def get_block(self):
        return self.block

    def set_before_competing(self):
        self.block.set_before_compete(
            hash_of_protocol=self.get_validity_protocol(),
            tats=self.tats,
            dict_of_bcws=self.dict_of_bcw,
            pubkey_dict=self.pubkey,
            # signature=DigitalSigner.sign_with_provided_privkey(
            #     dict_of_privkey_numbers={
            #         'x': 60785994004755780541968889462742035955235637618029604119657448498380482761088,
            #         'y': 100309319245511545150569175878829989424599308092677960010907323326738383429364,
            #         'd': 29950300400169917180358605208938775880760212514399944926857005417377480590100
            #     },
            #     message=json.dumps(self.tats).encode()
            # )

        )

    def set_after_competing(self, ):
        """
        after compete, create a GenesisBlockHeader instance, set the necessary attributes
        :return:
        """
        pass

    def compute_merkle_root(self):
        """
        uses the hashes of TAT, BCW and pubkey to produce a single merkle root hash

        A combined hash is used for competing, which is merkle root + hash of primary signatory's wallet
        :return:
        """
        list_of_hashes_for_merkle = list()
        tat_with_hash = dict()
        bcw_entry_with_hash = dict()

        # include hashes of token association transactions
        for tat in self.tats:
            temp_dict = {tat: self.tats[tat]}
            data = json.dumps(temp_dict).encode()
            hash_id = Hasher.sha_hasher(data=data)
            list_of_hashes_for_merkle.append(hash_id)
            tat_with_hash[hash_id] = temp_dict

        self.tats = tat_with_hash

        # include hash of BCW
        for bcw_entry in self.dict_of_bcw:
            temp_dict = {bcw_entry: self.dict_of_bcw[bcw_entry]}
            data = json.dumps(temp_dict).encode()
            hash_id = Hasher.sha_hasher(data=data)
            list_of_hashes_for_merkle.append(hash_id)
            bcw_entry_with_hash[hash_id] = temp_dict

        # include hash of pubkey
        data = json.dumps(self.pubkey).encode()
        hash_id = Hasher.sha_hasher(data=data)
        list_of_hashes_for_merkle.append(hash_id)



        print(list_of_hashes_for_merkle)

        if list_of_hashes_for_merkle:
            o = OrsesMerkleRootTree(items=sorted(list_of_hashes_for_merkle))
            o.create_merkle_tree()
            return o.get_merkle_root()

    @staticmethod
    def get_validity_protocol():
        data = FileAction.open_file_into_byte("Validity_Protocol", in_folder="Orses_Competitor_Core")

        return Hasher.sha_hasher(data=data, hash_form="b85_str")


if __name__ == '__main__':
    pass
    # gen_block = GenesisBlockCreator()
    # gen_block.set_before_competing()
    # block_0 = gen_block.block.__dict__
    #
    # [print(f"{i}: {block_0[i]}") for i in block_0]
    #
    # print(gen_block.merkle_root)