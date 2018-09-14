import time, random, pickle, json, enum, timeit

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
    def __init__(self, root_value: (int, float), blockNumber, blockForestInstance=None,saveToDatabase=False, forHash=True,
                 keepListRepr=True):
        """

        :param root_value: the first value, usually should be the hash of reward transactions
        :param saveToDatabase: if it is true, then a separate daemon process is created that saves data to database
        """
        self.block_number = blockNumber
        # self.forest_instance = blockForestInstance
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
        # self.list_repr = self.forest_instance.list_repr
        self.list_repr = [root_value]
        self.keep_list_repr = keepListRepr
        self.sorted_repr = {self.root: {"left": self.root.left, "right": self.root.right},
                            "max": self.root.value,
                            "min": self.root.value,
                            }

        self.saveToDatabase = saveToDatabase


    def get_min_value(self, a_root=None, get_node=False):
        min1 = self.root if a_root is None else a_root

        while True:
            if min1.left == None:
                return min1.value if not get_node else min1
            else:
                min1 = min1.left
                continue

    def max(self, get_node=False):
        max1 = self.root

        while True:
            if max1.right == None:
                return max1.value if not get_node else max1
            else:
                max1 = max1.right
                continue

    def get_sorted_repr(self):
        """
        First, check minimum
        second: append minimum and it's master's value only if minimum == master.left
        THen, check min minimum's master's right
        :return:
        """
        cur_node = self.get_min_value(get_node=True)
        tmp_list = [cur_node.value]

        while True:
            try:
                cur_node = cur_node.higher_valued_node
                tmp_list.append(cur_node.value)
                continue
            except AttributeError:
                break

        return tmp_list



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
                        self.list_repr.append(val) if self.keep_list_repr else None
                        return True
                    else:
                        current_node = current_node.right
                        continue
                elif compare_hex_string(val, current_node.value, BoolChoice.lesser):
                    if current_node.left is None:
                        current_node.insert_left(val)
                        self.list_repr.append(val) if self.keep_list_repr else None
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
                    if current_node.higher_valued_node is None:
                        current_node.higher_valued_node = current_node.right
                    else:
                        if current_node.higher_valued_node.value > current_node.right.value:
                            current_node.right.higher_valued_node,  current_node.higher_valued_node = \
                                current_node.higher_valued_node, current_node.right
                        else:
                            current_node.higher_valued_node = current_node.right
                    self.list_repr.append(val)

                    return
                else:
                    current_node = current_node.right
                    continue
            elif val < current_node.value:
                if current_node.left is None:
                    current_node.insert_left(val)
                    current_node.left.higher_valued_node = current_node
                    self.list_repr.append(val)
                    return
                else:
                    current_node = current_node.left
                    continue

    def check_val(self, val):
        # assert not self.forHash, "check_val() Not For Trees Storing Hashes, instead use instance method: check_hash()"
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

    def save(self):
        with open(f'{self.block_number}', "wb") as outFile:
            pickle.dump(self, outFile)

    @staticmethod
    def load(filename):

        with open(filename, "rb") as inFile:
            return pickle.load(inFile)

    class TreeNode:

        def __init__(self, val, search_tree, **kwargs):
            self.value = val
            self.left = kwargs["left"] if "left" in kwargs else None
            self.right = kwargs["right"] if "right" in kwargs else None
            self.master = kwargs["master"] if "master" in kwargs else None
            self.SearchTree = search_tree
            self.index = self.SearchTree.curr_index
            self.SearchTree.curr_index += 1
            self.lower_valued_node = None
            self.higher_valued_node = None

        def insert_left(self, val):

            self.left = self.SearchTree.TreeNode(val=val, master=self, search_tree=self.SearchTree)
            self.set_lower_or_higher(a_tree_node=self.left)

        def insert_right(self, val):
            self.right = self.SearchTree.TreeNode(val=val, master=self, search_tree=self.SearchTree)

            self.set_lower_or_higher(a_tree_node=self.right)

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

        def set_lower_or_higher(self, a_tree_node):
            current = self
            high = None
            low = None
            while True:
                if a_tree_node.value < current.value:
                    if current.lower_valued_node is None:
                        current.lower_valued_node = a_tree_node
                        a_tree_node.higher_valued_node = current
                        break
                    elif a_tree_node.value < current.lower_valued_node.value:
                        current = current.lower_valued_node
                        continue
                    else:  # if new node less than current but higher than current.lower_valued node
                        # assign current.lower to new nodes
                        # assign current as higher of new node
                        a_tree_node.lower_valued_node = current.lower_valued_node
                        a_tree_node.lower_valued_node.higher_valued_node = a_tree_node
                        a_tree_node.higher_valued_node = current
                        current.lower_valued_node = a_tree_node
                        break

                elif a_tree_node.value > current.value:

                    if current.higher_valued_node is None:
                        current.higher_valued_node = a_tree_node
                        a_tree_node.lower_valued_node = current
                        break
                    elif a_tree_node.value < current.higher_valued_node.value:
                        current = current.higher_valued_node
                        continue

                    else:  # new node is higher than current but lower than current.higher
                        a_tree_node.higher_valued_node = current.higher_valued_node
                        a_tree_node.higher_valued_node.lower_valued_node = a_tree_node
                        a_tree_node.lower_valued_node = current
                        current.higher_valued_node = a_tree_node
                        break


class BlockForest:
    def __init__(self, reward_tx: dict, blockNo: int):
        """
        each instance variable holds a BinarySearchTree for each type of Transacion, the block tree also holds a
        list of transactions which is appended by each
        :param reward_tx:
        """
        self.ttx = BinarySearchTree(root_value=reward_tx["tx_hash"], blockNumber=blockNo, blockForestInstance=self)
        self.trr = BinarySearchTree(root_value=reward_tx["tx_hash"], blockNumber=blockNo, blockForestInstance=self)
        self.trx = BinarySearchTree(root_value=reward_tx["tx_hash"], blockNumber=blockNo, blockForestInstance=self)
        self.nvc = BinarySearchTree(root_value=reward_tx["tx_hash"], blockNumber=blockNo, blockForestInstance=self)
        # self.main_tree = BinarySearchTree(root_value=reward_tx["tx_hash"], keepListRepr=True, blockNumber=blockNo)
        self.wallet_states = BinarySearchTree(root_value=reward_tx["tx_hash"], blockNumber=blockNo,
                                              blockForestInstance=self)
        self.list_repr = list()
        self.rwd_transaction = reward_tx
        self.isAccepting = True

    def insert(self, msg: dict):

        if self.isAccepting:  # if no more accepting  his happens when tree is closed and all
            if "ttx" in msg:  # transfer transaction
                self.ttx.insert_hash(msg["tx_hash"])
            elif "rvk_req" in msg:  # reservation revoke
                self.trx.insert_hash(msg["tx_hash"])
            elif "rsv_req" in msg:  # reservation request
                self.trr.insert_hash(msg["tx_hash"])
            elif "W_h_state" in msg: # wallet hash state
                self.wallet_states.insert_hash(msg["hash_state"])

            return True
        else:
            return False

    def check_if_in_forest(self, msg_hash, msg_type):
        if "ttx" == msg_type:  # transfer transaction
            self.ttx.check_hash(msg_hash)
        elif "rvk_req" == msg_type:  # reservation revoke
            self.trx.check_hash(msg_hash)
        elif "rsv_req" == msg_type:  # reservation request
            self.trr.check_hash(msg_hash)
        elif "W_h_state" == msg_type: # wallet hash state
            self.wallet_states.check_hash(msg_hash)

    def retrieve_and_close_forest(self):
        """
        this causes forest to stop accepting new value and send a concatenated list of all tx hashes
        This is used by OrsesMerkleRootTree class to create the merkle tree and get merkle root
        :return: list of tx_hashes
        """

        self.isAccepting = False
        return self.list_repr



if __name__ == '__main__':

    import pickle

    with open("binary_pickled", "rb") as infile:
        tree = pickle.load(infile)
    # with open("json_file", "r") as injson:
    #     list1 = json.load(injson)
    #
    #     print(list1)


#     import pickle
#     the_tree = BinarySearchTree(
#         blockNumber=False,
#         root_value=3750000,
#         forHash=False
#     )
#     list1 = [3750000]
#
#     for i in range(500000):
#         value = random.randint(0, 7500000)
#         list1.append(value)
#         the_tree.insert(value)
#
#     with open("binary_pickled", 'wb') as pickleOutfile:
#         pickle.dump(the_tree, pickleOutfile)
#
#     with open("json_file", "w") as jsonoutfile:
#         json.dump(list1, jsonoutfile)
#
#     # print(the_tree.get_sorted_repr())
#     # print(list1)
#     # print(set(list1))
#     print("Started TIming")
#     bSearch_str = \
#     """
# the_tree.get_sorted_repr()
#         """
#
#     set_str = \
#         """
# sorted(list1)
#             """
#
#     timer = timeit.Timer(bSearch_str, "import random\nfrom __main__ import the_tree")
#
#     timer1 = timeit.Timer(set_str, "import random\nfrom __main__ import the_tree, list1")
#
#
#     print(timer.timeit(50))
#     print(timer1.timeit(50))