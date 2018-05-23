"""
Holds Merkle root tree
"""

from Crypto.Hash import SHA256

class Row:
    def __init__(self):
        self.row = list()

    def hashing(self, first: str, second: str):
        return SHA256.new(f'{first}{second}'.encode()).hexdigest()

    def hash_rows(self, items):
        len_list = len(items)
        if len_list > 1:
            if len_list % 2 == 0:
                # each item will have a partner
                for i in range(1, len_list, 2):
                    self.row.append(self.hashing(items[i-1], items[i]))
            else:
                # the last item, wont have a partner, so hash it to itself

                for i in range(1, len_list, 2):
                    self.row.append(self.hashing(items[i-1], items[i]))

                    self.row.append(self.hashing(items[-1], items[-1]))

        elif len_list == 1:
            self.row.append(self.hashing(items[0], items[0]))  # if only one item in list, hash itself

        return self.row


class OrsesMerkleRootTree:

    def __init__(self, items):
        self.items_to_include_in_tree = items
        self.tree = {

        }
        self.merkle_root = None

    def create_merkle_tree(self):
        count = 1
        items = self.items_to_include_in_tree

        while True:
            if len(items) == 1:
                self.merkle_root = items[0]
                return self.merkle_root
            items = Row().hash_rows(items)
            self.tree[count] = items
            count += 1







if __name__ == '__main__':
    list1 = ["s", "b", "c", "d", "ff", "pf"]

    merkle_tree = OrsesMerkleRootTree(list1)
    merkle_tree.create_merkle_tree()

    print(merkle_tree.merkle_root)
    print(merkle_tree.tree)