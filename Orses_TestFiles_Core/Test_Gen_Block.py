from Orses_Cryptography_Core.Hasher import Hasher

import time, json


gen_block = {'timestamp': 1521468548,
             'TAT': {'Wa0bb0a8bb0af0564ca28ff81fec0eb3220407c76': 5000000.0,
                     'W11f4aa963b79a28eb7039097330ece1f67477e59': 1400000.0},
             'Sha256': '1608320dafe2f743194c4a8fce9b68532d70c604f3b9a25b7699d7e34144d96e'}


token_association_transactions = dict()

token_association_transactions["Wa0bb0a8bb0af0564ca28ff81fec0eb3220407c76"] = 5000000.00
token_association_transactions["W11f4aa963b79a28eb7039097330ece1f67477e59"] = 1400000.00


# if updating using this
def create_test_genesis_block():

    genesis_block = dict()
    genesis_block["timestamp"] = int(time.time())
    genesis_block["TAT"] = token_association_transactions
    genesis_block["Sha256"] = Hasher.sha_hasher(json.dumps(genesis_block["TAT"]))

    return genesis_block


if __name__ == '__main__':
    print(create_test_genesis_block())