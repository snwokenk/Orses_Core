import time, random, pickle, json, enum

"""
holds BinarySearchTree
"""


# ********  helper functions and classes *****
class BoolChoice(enum.Enum):
    equal = "equal"
    greater = "greater"
    lesser = "lesser"


def hex_to_int(hex_string):

    return int(hex_string, 16)


def compare_hex_string(hex1, hex2, compare: BoolChoice):
    """
    this essentially does:
    hex1 > hex2
    hex1 < hex2
    hex1 == hex2

    :param hex1: left hex
    :param hex2: right hex
    :param compare: must be a member of Boolchoice enum class
    :return:
    """

    return int(hex1, 16) == int(hex2, 16) if compare == BoolChoice.equal else\
    (int(hex1, 16) > int(hex2, 16) if compare == BoolChoice.greater else
     (int(hex1, 16) < int(hex2, 16) if compare == BoolChoice.lesser else None))


class BinarySearchTree:
    def __init__(self, root_value: (int, float), saveToDatabase=False, forHash=True):
        """

        :param root_value: the first value, usually should be the hash of reward transactions
        :param saveToDatabase: if it is true, then a separate daemon process is created that saves data to database
        """
        self.forHash = forHash
        if self.forHash is True:
            assert isinstance(root_value, str), "must be a hex string"
            try:
                int(root_value, 16)
            except ValueError:
                raise Exception("must be a hex string")
        else:
            assert isinstance(root_value, int)
        self.curr_index = 0
        self.root = self.TreeNode(root_value, search_tree=self)
        self.list_repr = [self.root]
        self.sorted_repr = {self.root: {"left": self.root.left, "right": self.root.right},
                            "max": self.root.value,
                            "min": self.root.value,
                            }
        self.saveToDatabase = saveToDatabase

    def insert_hash(self, val: str):
        assert self.forHash, "insert_hash() Not For Trees Storing ints, instead use instance method: insert()\n" \
                             "if You would like to store hashes set forhash parameter of BinarySearchTree to True"
        current_node = self.root

        try:
            int(val, 16)  # checks to make sure it's a hexadecimal, if not will raise ValueError
            while True:
                if compare_hex_string(val, current_node.value, BoolChoice.equal):
                    return False
                if compare_hex_string(val, current_node.value, BoolChoice.greater):
                    if current_node.right is None:
                        current_node.insert_right(val)
                        self.list_repr.append(val)
                        return True
                    else:
                        current_node = current_node.right
                        continue
                elif compare_hex_string(val, current_node.value, BoolChoice.lesser):
                    if current_node.left is None:
                        current_node.insert_left(val)
                        self.list_repr.append(val)
                        return True
                    else:
                        current_node = current_node.left
                        continue
        except ValueError:
            return None

    def check_hash(self, val):
        assert self.forHash, "check_hash() Not For Trees Storing ints, instead use instance method: check_val()"
        current_node = self.root

        try:
            int(val, 16)  # checks to make sure it's a hexadecimal, if not will raise ValueError
            while True:
                if compare_hex_string(val, current_node.value, BoolChoice.equal):
                    return True
                if compare_hex_string(val, current_node.value, BoolChoice.greater):
                    if current_node.right is None:
                        return False
                    else:
                        current_node = current_node.right
                        continue

                elif compare_hex_string(val, current_node.value, BoolChoice.lesser):
                    if current_node.left is None:
                        return False
                    else:
                        current_node = current_node.left
                        continue
        except ValueError:
            return None

    def insert(self, val):
        assert not self.forHash, "insert() Not For Trees Storing Hashes, instead use instance method: insert_hash()\n" \
                                 "if You would like to store INTS, set forhash parameter of BinarySearchTree to False"
        current_node = self.root
        while True:
            if val == current_node.value:
                return "already inserted"
            if val > current_node.value:
                if current_node.right is None:
                    current_node.insert_right(val)
                    self.list_repr.append(val)
                    return
                else:
                    current_node = current_node.right
                    continue
            elif val < current_node.value:
                if current_node.left is None:
                    current_node.insert_left(val)
                    self.list_repr.append(val)
                    return
                else:
                    current_node = current_node.left
                    continue

    def check_val(self, val):
        assert not self.forHash, "check_val() Not For Trees Storing Hashes, instead use instance method: check_hash()"
        current_node = self.root
        while True:
            if val == current_node.value:
                return True
            if val > current_node.value:
                if current_node.right is None:
                    return False
                else:
                    current_node = current_node.right
                    continue

            elif val < current_node.value:
                if current_node.left is None:
                    return False
                else:
                    current_node = current_node.left
                    continue



    def get_list_of_items(self):
        return self.list_repr

    def __contains__(self, item):
        return self.check_val(item)

    def __iter__(self):
        return iter(self.list_repr)

    def get_curr_index(self):
        return self.curr_index

    class TreeNode:

        def __init__(self, val, search_tree, **kwargs):
            self.value = val
            self.left = kwargs["left"] if "left" in kwargs else None
            self.right = kwargs["right"] if "right" in kwargs else None
            self.master = kwargs["master"] if "master" in kwargs else None
            self.SearchTree = search_tree
            self.index = self.SearchTree.curr_index
            self.SearchTree.curr_index += 1

        def insert_left(self, val):

            self.left = self.SearchTree.TreeNode(val=val, master=self, search_tree=self.SearchTree)

        def insert_right(self, val):
            self.right = self.SearchTree.TreeNode(val=val, master=self, search_tree=self.SearchTree)

        def insert(self, val):  # recursive insert
            if val == self.value:
                return False
            elif val < self.value:
                self.left.insert(val) if self.left else self.insert_left(val)
            elif val > self.value:
                self.right.insert(val) if self.right else self.insert_right(val)

        def value_in_tree(self, val):  # recursive check
            if val == self.value:
                return True
            elif val < self.value:
                return self.left.value_in_tree if self.left else False
            elif val > self.value:
                return self.right.value_in_tree if self.right else False


class BlockTree:
    def __init__(self, reward_tx: dict):
        """
        each instance variable holds a BinarySearchTree for each type of Transacion, the block tree also holds a
        list of transactions which is appended by each
        :param reward_tx:
        """
        self.ttx = BinarySearchTree()
        self.trr = BinarySearchTree()
        self.trx = BinarySearchTree()
        self.wallet_states = BinarySearchTree()
        self.rwd_transaction = reward_tx
if __name__ == '__main__':
    pass