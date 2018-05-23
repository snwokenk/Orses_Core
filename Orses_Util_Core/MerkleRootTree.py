"""
Holds Merkle root tree

if (len_list % 4 == 0 and len_list % 3 != 0) then each node will have a partner
"""

from Crypto.Hash import SHA256


def hashing(first: str, second: str):
    return SHA256.new(f'{first}{second}'.encode()).hexdigest()




class Node:
    """
    this class represents a leef node in the tree
    with this node
    """
    def __init__(self,hash_value):
        """

        :param partner: the other partner who hash is concatenated to produce hash of master
        :param hash_value: hash value
        """
        self.hash_value = hash_value
        self.partner = None
        self.master = None
        self.children = list()  # no more than 2 children, if 1 child, then created by duplicating one hash

    def set_partner_and_master(self, partner, master):
        assert isinstance(partner, Node)
        self.partner = partner
        self.master = master


class OrsesMerkleRootTree:
    # todo: create a merkle tree dict of each leaf node as keys and list of hashes needed as value
    # todo:

    def __init__(self, items):

        # the tree leafs
        self.items_to_include_in_tree = items

        self.tree = {
        }

        # will store each transaction hash with it's LeafNode instance, this node can be used to get a list of hashes
        # to prove that transaction is part of merkle tree
        self.dict_of_leaf_nodes = dict()
        self.dict_of_other_nodes = dict()

        # the single hash derived from all hashes
        self.merkle_root = None

    def create_merkle_tree(self):
        count = 1
        items = self.items_to_include_in_tree

        while True:
            if len(items) == 1:
                self.merkle_root = items[0]
                return self.merkle_root
            self.tree[count] = items = self.hash_rows(items)
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

        if count == 1:  # create the initial leaf node dictionary
            if len_list > 1:
                if len_list % 2 == 0:
                    # each item will have a partner
                    for i in range(1, len_list, 2):
                        hash_value = hashing(items[i-1], items[i])
                        self.dict_of_other_nodes[hash_value] = Node(hash_value)
                        self.dict_of_leaf_nodes[items[i-1]] = Node(items[i-1])
                        self.dict_of_leaf_nodes[items[i]] = Node(items[i])
                        self.dict_of_leaf_nodes[items[i-1]].set_partner(self.dict_of_leaf_nodes[items[i]],
                                                                        self.dict_of_other_nodes[hash_value])
                        self.dict_of_leaf_nodes[items[i]].set_partner(self.dict_of_leaf_nodes[items[i-1]],
                                                                      self.dict_of_other_nodes[hash_value])


                else:
                    # the last item, wont have a partner, so hash it to itself

                    for i in range(1, len_list, 2):
                        hash_value = hashing(items[i-1], items[i])
                        self.dict_of_other_nodes[hash_value] = Node(hash_value)
                        self.dict_of_leaf_nodes[items[i-1]] = Node(items[i-1])
                        self.dict_of_leaf_nodes[items[i]] = Node(items[i])
                        self.dict_of_leaf_nodes[items[i-1]].set_partner(self.dict_of_leaf_nodes[items[i]],
                                                                        self.dict_of_other_nodes[hash_value])
                        self.dict_of_leaf_nodes[items[i]].set_partner(self.dict_of_leaf_nodes[items[i-1]],
                                                                      self.dict_of_other_nodes[hash_value])
                    hash_value = hashing(items[-1], items[-1])
                    self.dict_of_other_nodes[hash_value] = Node(hash_value)
                    self.dict_of_leaf_nodes[items[-1]] = Node(items[-1])
                    self.dict_of_leaf_nodes[items[-1]].set_partner_and_master(None,
                                                                              self.dict_of_other_nodes[hash_value])


            elif len_list == 1:
                row.append(hashing(items[0], items[0]))  # if only one item in list, hash itself

        else:  # create only non leaf nodes
            if len_list > 1:
                if len_list % 2 == 0:
                    # each item will have a partner
                    for i in range(1, len_list, 2):
                        row.append(hashing(items[i-1], items[i]))
                else:
                    # the last item, wont have a partner, so hash it to itself

                    for i in range(1, len_list, 2):
                        row.append(hashing(items[i-1], items[i]))
                    row.append(hashing(items[-1], items[-1]))
            elif len_list == 1:
                row.append(hashing(items[0], items[0]))  # if only one item in list, hash itself

        return row







if __name__ == '__main__':
    list1 = ["s", "b", "c", "d", "ff", "pf"]

    merkle_tree = OrsesMerkleRootTree(list1)
    merkle_tree.create_merkle_tree()

    print(merkle_tree.merkle_root)
    print(merkle_tree.tree)