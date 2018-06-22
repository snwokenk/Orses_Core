"""
Holds Merkle root tree

if (len_list % 4 == 0 and len_list % 3 != 0) then each node will have a partner
"""
import time
from Crypto.Hash import SHA256


def hashing(left: str, right: str):
    return SHA256.new(f'{left}{right}'.encode()).hexdigest()


class Node:
    """
    this class represents a leef node in the tree
    with this node
    """
    def __init__(self,hash_value, position):
        """

        :param partner: the other partner who hash is concatenated to produce hash of master
        :param hash_value: hash value
        """
        self.hash_value = hash_value
        self.partner = None
        self.master = None
        self.position = position  # either "l" for left, or "r" for right. dictates how to concatenate

    def set_partner_and_master(self, partner, master):
        if partner:
            assert isinstance(partner, Node)
        self.partner = partner
        self.master = master


class OrsesMerkleRootTree:

    def __init__(self, items):

        # the tree leafs
        self.items_to_include_in_tree = items

        self.tree = {
        }

        self.dict_of_leaf_nodes = dict()   # dict storing the leaf nodes (nodes with tx hash value)
        self.dict_of_other_nodes = dict()  # dict storing non leaf nodes (nodes with hash from other hash)

        self.merkle_root = None  # the single hash derived from all hashes. gotten when merkle tree is created

    def get_branch_for_proof(self, leaf_node_hash):
        """
         a list of hashes/none objects are returned;
         To use:
         the first index is the other leaf node partner hashed (if it is none, it means it had no partner so duplicated
         the second index is hashed with the hashes derived from hashing the first index with the leaf node

         ie:
         merkle_root = 545f2a819435c7b05d4d063e9fd088327ee92ecd7d721c3bc5a15b4577ebbf33
         tx_hash = 961b6dd3ede3cb8ecbaacbd68de040cd78eb2ed5889130cceb4c49268ea4d506
         proof_list = [
            21e721c35a5823fdb452fa2f9f0a612c74fb952e06927489c6b27a43b817bed4,
            6cad86e09fea5bc1452330a4d406f4060d8c7e66d4243455deeed29097fc295a
         ]

         to get the first hash =
         SHA256 f'{tx_hash}{proof_lis[0]}'.encode if the the first item in the list is NOT none. if it is then
         SHA256 f'{tx_hash}{tx_hash'.encode

         to get the second hash =
         SHA256 f'{first hash}{proof_lis[1]}'.encode() if second item in lien is None object then
         SHA256 f'{first_hash}{first_hash}'.encode() (since the second item is last item, IT SHOULD NOT BE NONE)
         first_hash:
            7be602ea49a0bd5e48b1f9fff6dde54a13f3a8c010d5098ae40cea5f400d06c3
         second hash(since last this should hash == merkle root):





        :param leaf_node_hash: the transaction hash, using this hash a list of hashes/None objects are returned
        :return: list of hashes/None objects
        """

        curr_node = self.dict_of_leaf_nodes[leaf_node_hash]
        proof_list = list()
        while curr_node is not None:
            proof_list.append([curr_node.partner.position, curr_node.partner.hash_value]) if curr_node.partner \
            is not None else (proof_list.append(None) if curr_node.master is not None else None)
            curr_node = curr_node.master

        return proof_list

    @staticmethod
    def validate_branch_for_proof(leaf_node_hash, proof_list, merkle_root):
        """
        used to validate that the tx hash is part of the merkle root by recreating
        :param leaf_node_hash:
        :param proof_list:
        :return:
        """
        current_hash = leaf_node_hash
        for i in proof_list:
            if i is None:
                current_hash = hashing(current_hash, current_hash) # none means to duplicate current hash and hash
            else:
                if i[0] == "r":
                    current_hash = hashing(current_hash, i[1])
                elif i[0] == "l":
                    current_hash = hashing(i[1], current_hash)

        # current_hash should be equal to merkle_root at the end of the loop
        return current_hash == merkle_root

    def create_merkle_tree(self):
        count = 1
        items = self.items_to_include_in_tree

        while True:
            self.tree[count] = items = self.hash_rows(items, count)
            if len(items) == 1:
                self.merkle_root = items[0]
                return self.merkle_root

            count += 1

    def get_merkle_root(self):
        return self.merkle_root

    def hash_rows(self, items: list, count=1):
        """
        if count is one create initial leaf nodes, else
        :param items: list of transaction hashes(if count 1) or list of hashes of hashes
        :param count:
        :return:
        """
        row = list()
        len_list = len(items)

        if count == 1:  # create the initial leaf node dictionary/self.dict_of_leaf_nodes
            if len_list > 1:

                # each item will have a partner
                for i in range(1, len_list, 2):
                    hash_value = hashing(items[i-1], items[i])
                    row.append(hash_value)
                    self.dict_of_other_nodes[hash_value] = Node(hash_value, None)
                    self.dict_of_leaf_nodes[items[i-1]] = Node(items[i-1], "l")
                    self.dict_of_leaf_nodes[items[i]] = Node(items[i], "r")
                    self.dict_of_leaf_nodes[items[i-1]].set_partner_and_master(self.dict_of_leaf_nodes[items[i]],
                                                                               self.dict_of_other_nodes[hash_value])

                    # print("master: ", self.dict_of_other_nodes[hash_value], vars(self.dict_of_leaf_nodes[items[i-1]]))


                    self.dict_of_leaf_nodes[items[i]].set_partner_and_master(self.dict_of_leaf_nodes[items[i-1]],
                                                                             self.dict_of_other_nodes[hash_value])
                # print("here: ",  vars(self.dict_of_leaf_nodes["961b6dd3ede3cb8ecbaacbd68de040cd78eb2ed5889130cceb4c49268ea4d506"]))

                if len_list % 2 != 0:  # if true, the last item in index -1 was missed, so duplicate and hash
                    hash_value = hashing(items[-1], items[-1])
                    row.append(hash_value)
                    self.dict_of_other_nodes[hash_value] = Node(hash_value, None)
                    self.dict_of_leaf_nodes[items[-1]] = Node(items[-1], None)
                    self.dict_of_leaf_nodes[items[-1]].set_partner_and_master(None,
                                                                              self.dict_of_other_nodes[hash_value])
            elif len_list == 1:
                row.append(hashing(items[0], items[0]))  # if only one item in list, hash itself

            else:
                return []

        else:  # create only non leaf nodes/self.dict_of_other_nodes
            if len_list > 1:

                for i in range(1, len_list, 2):
                    hash_value = hashing(items[i-1], items[i])
                    row.append(hash_value)
                    self.dict_of_other_nodes[hash_value] = Node(hash_value, None)
                    self.dict_of_other_nodes[items[i-1]].set_partner_and_master(self.dict_of_other_nodes[items[i]],
                                                                               self.dict_of_other_nodes[hash_value])
                    self.dict_of_other_nodes[items[i-1]].position = "l"
                    self.dict_of_other_nodes[items[i]].set_partner_and_master(self.dict_of_other_nodes[items[i-1]],
                                                                             self.dict_of_other_nodes[hash_value])
                    self.dict_of_other_nodes[items[i]].position = "r"

                if len_list % 2 != 0:  # if true, the last item in index -1 was missed, so
                    hash_value = hashing(items[-1], items[-1])
                    row.append(hash_value)
                    self.dict_of_other_nodes[hash_value] = Node(hash_value, None)

                    # this is assuming that node already created in previous hash round
                    self.dict_of_other_nodes[items[-1]].set_partner_and_master(None,
                                                                               self.dict_of_other_nodes[hash_value])
                    # position is already none, so leave it at none

            elif len_list == 1:
                row.append(hashing(items[0], items[0]))  # if only one item in list, hash itself

            else:
                return []

        return row





if __name__ == '__main__':

    list1 = {
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
    }

    merkle_tree = OrsesMerkleRootTree(list(list1))
    merkle_tree.create_merkle_tree()

    print(merkle_tree.merkle_root)
    # print(merkle_tree.tree, "\n")

    tx_to_validate = "feaa53609b4265078f8cef123ba43e01cc2ca6871f05bea9efafa6133a9914c5"
    #
    proof_list1 = merkle_tree.get_branch_for_proof(tx_to_validate)
    print("----------")
    print(proof_list1)
    print("**********")
    isValidated = merkle_tree.validate_branch_for_proof(
        leaf_node_hash=tx_to_validate,
        merkle_root="456f4f16b6abbcd4ee4f06e0f96c511c8731ee8b77e68fe7ab25fc6e8171bfa2",
        proof_list=proof_list1
    )

    print(isValidated)