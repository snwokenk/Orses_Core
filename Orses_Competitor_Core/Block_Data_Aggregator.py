from Orses_Database_Core.RetrieveData import RetrieveData
import time, random
"""
https://en.bitcoin.it/wiki/Block_hashing_algorithm
https://en.bitcoin.it/wiki/Block
"""
"""
    used to gather all data needed to create a block

    Structure of Block (block_number not in {0,1}:
    pb_n example: "F7+2+0A' example of a valid hash would start with  FFFFFFFF, FFFFFFF0, FFFFFFFA.
                'F7' means F must occupy the AT LEAST the first 7 characters in a hash
                '2' means 2 additional characters are allowed after any leading 7
                "0A" means character 0 (zero) and A are the additional characters.
                these 2 additonal characters only allowed after the minimum leading prime characters
                
                so this is invalid 'FF0FFFF----' first 7 characters must be the prime char which in example is F
                This is valid - FFFFFFFAF - first 7 characters are prime char.
                
    Calc Hash Score:
        Hash scores are calculated using the characters after the required leading prime char a:
        ie: FFFFFFFAF  in this case AF and any other character after is added to the probability score. 
        If A's value is 14 and F's value is 15 then score is 16^7+14+15+(sum of other values)
        ie: FFFFFFFFA  hash starts wih 8 leading F or prime char, so rather than adding the 15 score is 16^8+14+(sum of other values)
        
        Hash score rewards hashes with more than the required leading characters
    
    **** EXAMPLE BLOCK ******
    {
    block_H: {hex block_id: hexadecimal repr of block number,
                version: version_number_of_software,
                time: current time,
                fees_earned: fee's to be earned if creator becomes primary signatory
                nonce: 
                comp_params: {
                    pb_n:ie 'F7+3+0AB' F is prime char, 7 is leading prime chars in hash, 3 is # of add_character, 0, A,B
                         are the 3 additional characters (prime & addl chars are from the previous 3rd block ie. if current
                         block_id is 10, the winning block with block_id 7 determines the prime/addl chars.
                         
                         The maximum probability is the lower 1 standard deviation of the average of probabilities of 
                         primary and secondary signatories of the last 3 blocks or 3 competitions. The maximum 
                         probability is used to determining number of leading prime characters and additional characters
                    hex_shuf: number keys from 0-15 and hex value. If block is winning block hex char at 15 becomes prime
                              char at block_id == block_id + 3

                }
            }
    w_h_state: sha256 hash states of connected wallets set, number_of_asgn_stmts, fees.
               [sha256_merkle_root, # of asgn_stmts, fee_to_block_creator]
    txs: {
        ttx: transfer transactions set,
        trr: token reservation request set,
        trx: token reservation revoke set,
        nvc: new valid competitors set
        }


    },
    rwd: set of reward transactions, rewarding self and rewarding previous reference block creators
    no_txs: number of transactions (sum of number of asgn_stmts, ttx, trr, trx]
    """


class BlockAggregator:

    def __init__(self, block_id, software_version, wid):

        self.new_block = {"block_h": {"block_id": block_id, 'version': software_version, "time": int(time.time()),
                                      "fees_earned": 0, "comp_params": dict()},
                          "w_h_state": dict(),
                          "txs": {"ttx": set(), "trr": set(), "trx": set(), "nvc": set()},
                          "rwd": dict(),
                          "txs_no": 0,



                          }
        self.previous_block = RetrieveData.get_previous_block()

    def create_block(self):
        """
        used to create block
        :return:
        """

    def determine_competition_length(self):
        """
        used to determine the length competition 30, 60 or 90 seconds from previous block
        :return:
        """

    def hex_shuffle(self):
        """
        shuffles the hex values, Hex character with value 15 is used as prime character if block is signatory block
        and if any additional characters are needed then the next characters with the highest values are chosen
        :return:
        """

        hex_char = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]
        random.shuffle(hex_char) # shuffles hex_char
        hex_char = {x:y for x, y in enumerate(hex_char)}  # assign value to shuffled hex character

        self.new_block["block_h"]["comp_params"]["hex_shuf"] = hex_char
        return True

    def determine_min_statistical_difficulty(self):
        """
        used to determine minimum statistical difficulty from previous block
        :return:
        """

    def reward_previous_secondary_signatory(self):
        """
        will get data of previous secondary signatories and include in block
        :return:
        """

    def reward_self(self):
        """
        will reward self based on the current valid rewards.
        :return:
        """

    def create_reward_transactions(self):
        """
        creates and sets reward transactions
        :return:
        """

    def set_valid_transfer_transactions(self):
        """
        used to set update current block with valid
        :return:
        """
        d = RetrieveData.get_valid_transfer_transactions()
        self.new_block["block_h"]["fees_earned"] += sum(d[k][1]['fee'] for k in d) if d else 0
        self.new_block["txs"]["ttx"] = d

    def set_valid_wallet_hash_state(self):
        """
        used to set or update wallet hash state of block
        :return:
        """

    def set_valid_token_reservation_request(self):
        """
        used to set or update trr section of block
        :return:
        """
        d = RetrieveData.get_token_reservation_requests()
        self.new_block["block_h"]["fees_earned"] += sum(d[k][1]['fee'] for k in d) if d else 0

        self.new_block["txs"]["trr"] = d

    def set_valid_token_reservation_revoke(self):
        """
        used to set or update trx section of block
        :return:
        """

    def set_valid_new_verinode_competitor(self):
        """
        adds a valid competitor
        :return:
        """

    def set_number_of_transactions(self):
        """
        used to set number of transactions
        :return:
        """

        self.new_block['txs_no'] = len(self.new_block["w_h_state"]) + len(self.new_block["txs"]["ttx"]) + \
                                   len(self.new_block["txs"]["trr"]) + len(self.new_block["txs"]["trx"]) + \
                                   len(self.new_block["txs"]["nvc"])

