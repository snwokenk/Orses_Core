from Orses_Competitor_Core.Block_Data_Aggregator import GenesisBlock, GenesisBlockHeader
from Orses_Util_Core.FileAction import FileAction
from Orses_Cryptography_Core.Hasher import Hasher
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Crypto.Hash import SHA256
from collections import Iterable
from Orses_Util_Core.MerkleRootTree import OrsesMerkleRootTree


import json


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
    block_0 = gen_block.block.__dict__

    [print(f"{i}: {block_0[i]}") for i in block_0]