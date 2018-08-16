from Orses_Database_Core.RetrieveData import RetrieveData
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData
from collections import Iterable

import time, random, statistics, math

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
    rwd: dict of reward transactions, rewarding self and rewarding previous reference block creators
    no_txs: number of transactions (sum of number of asgn_stmts, ttx, trr, trx]
    """


def hex_to_int(hex_string):
    return int(hex_string, 16)

# ****  Class Representing Block Headers  **** #


class BaseBlockHeader:
    def __init__(self):
        self.block_no = None  # hex number without the 0x
        self.block_hash = None  # valid hash of block
        self.mrh = None  # Merkle root
        self.n = None  # nonce
        self.x_n = None  # extra nonce
        self.p_s = None  # primary signatory

        self.mpt = None  # maximum probability target
        self.shv = None  # shuffled hex values
        self.time = int(time.time())  # time in hex value

    def __call__(self, *args, **kwargs):
        pass

    def get_block_header(self):
        return self.__dict__

    def set_block_no(self, block_number: int):
        self.block_no = format(block_number, "x")

    def set_block_hash(self, block_hash):
        """
        :param block_hash: the hash meeting or beating the required probability target set by the winner of
                            the previous block
        :return: none
        """
        self.block_hash = block_hash

    def set_merkle_root(self, merkle_root: str):

        if isinstance(merkle_root, str) and self.mrh is None:
            self.mrh = merkle_root

    def set_nonce(self, nonce: (int, float)):

        self.n = nonce

    def set_extra_nonce(self, x_nonce: (int, float)):
        self.x_n = x_nonce

    def set_primary_signatory(self, primary_signatory):
        self.p_s = primary_signatory

    def set_maximum_probability_target(self, probability_of_5_runnerups: Iterable):

        """


        ******** READ FOR EXPLANATION *******
        In Plain English a prob notation of an example P7+3:

        for the P7:
        means the prime character which is chosen randomly must appear 7 times in front of hash. if it was p8+3 it
        would mean the prime character must appear 8 times and if it was p9+3 then it must appear 9 times. ie going with
        the original example of p7+3 and assuming the prime character if 'f'
        the first 7 characters of a 64 character sha256 hash would look like:
        fffffff--

        for the +3:
        This means that after the initial required number of prime characters the characters after can include
        the prime and 2 additional characters. if the example was p7+4 the prime char and 3 additional if the example
        was p7+5 then prime char and 4 additional chars

        using the original example of p7+3 with prime as f and assuming 2 additional char are 'e' and 'd'.
        then valid hashes must start with:
        fffffffd
        fffffffe
        ffffffff

        Also as long as the character sequences arent broken, the probabilty score of each hash is added:

        for example: assuming p7+3
        hash of : fffffffeeeee OR fffffffffedeff will be calculated as sum of 16**7 power for the first 7 char and then
                  (16/3)**5 (valid characters come up consecutively 5 times.

        For the finding the probability valid characters must appear CONSECUTIVELY so a hash of fffffffdeaf will only
        use fffffffde portion for probability calculations and ignore anything that comes after the 'a'


        IN explaining this: IT is not common to see +1. to demonstrant p7+1 == p8+0

        ********

        returns a string probability notation P{no of leading primes expected} + {no of chars allowed after leading primes}

        an example if probability notation is 'P7+6'

        for 'P7+6'
        The the probability is (6**7) * (16/6) == 1 in 715,827,883

        for "P8+4'
        The the probability is (6**8) * (16/4) == 1 in 17,179,869,184

        The theoretical max of notation (no_of_prime_chars_req) p64+0 and the max of the (no_of_sec_chars_accepted) 15

        :param probability_of_5_runnerups: list of top 5 lowest probability, lowest prob == greatest number. each item
                                            is in a prob_notation ie 'p7+0' or 'p8+3' etc
        :return:
        """

        def determine_probability_from_notation(prob_notation: str):

            # remember P(whatever) + 1 is the same as P{whatever+1} + 0
            # ie P7+1 == p8+0

            temp_list = prob_notation.split(sep='+')
            first_variable = int(temp_list[0][1:])
            second_variable = int(temp_list[1])

            prime_prob = 16 ** first_variable
            addl_prop = (16 / second_variable) if 0 < second_variable < 16 else 0

            return prime_prob * addl_prop if addl_prop > 0 else prime_prob

        try:
            temp_list = [determine_probability_from_notation(prob_notation) for prob_notation in probability_of_5_runnerups]

        except AttributeError as e:
            print(f"error in {__file__}, might be prob_notation not str: {e}")
        except ValueError as e:
            print(f"error in {__file__}, might be prob_notation not in P(int)+(int) ie P7+3: {e}")
        else:

            probability_of_5_runnerups = temp_list

            try:
                average = statistics.mean(probability_of_5_runnerups)
                stdv = statistics.pstdev(probability_of_5_runnerups, mu=average)
                minProb = min(probability_of_5_runnerups)
            except statistics.StatisticsError:
                return None
            else:

                max_prob_targ = math.floor(average) - math.floor(stdv)
                if max_prob_targ < minProb:
                    max_prob_targ = minProb  # might be a large number rep probabilitty  4294967296 = 1/4294967296

                # find log base 16 of max prob targ
                mpt_log_base_16 = math.log(max_prob_targ, 16)

                # subtract decimal and save both
                decimal_log = mpt_log_base_16 - math.floor(mpt_log_base_16)

                no_of_prime_chars_req = abs(mpt_log_base_16 - decimal_log)

                if decimal_log > 0:
                    no_of_sec_chars_accepted = math.ceil(16/(16**decimal_log))
                else:
                    no_of_sec_chars_accepted = 0

                # turn to Orses notation

                prob_notation = f"P{int(no_of_prime_chars_req)}+{no_of_sec_chars_accepted}"

                return prob_notation

    def set_shuffled_hex_values(self):
        """
        shuffles the hex values, Hex character with value 15 is used as prime character if block is signatory block
        and if any additional characters are needed then the next characters with the highest values are chosen
        :return:
        """
        if self.shv is None:
            hex_char = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]
            random.shuffle(hex_char) # shuffles hex_char in place
            hex_char = {x+1: y for x, y in enumerate(hex_char)}  # assign value to shuffled hex character

            self.shv = hex_char


class RegularBlockHeader(BaseBlockHeader):

    def __init__(self):
        super().__init__()
        self.p_h = None  # previous hashes of past 2 blocks

    def set_previous_2_hashes(self, list_of_prev_2_hashes):
        self.p_h = list_of_prev_2_hashes


class BlockOneHeader(BaseBlockHeader):
    def __init__(self):
        super().__init__()



class GenesisBlockHeader(BaseBlockHeader):

    def set_header_before_comepete(self, primary_sig_wallet_id, merkle_root):
        self.set_block_no()
        self.set_primary_signatory(primary_sig_wallet_id=primary_sig_wallet_id)
        self.set_shuffled_hex_values()
        self.set_maximum_probability_target()
        self.set_merkle_root(merkle_root=merkle_root)

    def set_block_no(self, block_number=0):
        self.block_no = format(0, "x")

    def set_primary_signatory(self, primary_sig_wallet_id):
        self.p_s = primary_sig_wallet_id

    def set_maximum_probability_target(self, prob_of_5_runnerups='P6+0'):
        self.mpt = prob_of_5_runnerups  # for Genesis Block


# **** Class Representing Blocks **** #


class BaseBlock:
    def __init__(self):
        self.bh = None  # block header
        self.s_s = None  # secondary signatories

    def get_block(self):
        return self.__dict__


class GenesisBlock(BaseBlock):
    def __init__(self):
        super().__init__()
        self.tats = None  # token association transaction
        self.sig = None  # b85 string
        self.vph = None  # validity protocol
        self.pubkey = None  # pubkey dict with x and y
        self.bcws = None  # genesis blockchain connected wallets

    def set_after_compete(
            self,
            block_header: GenesisBlockHeader,
            list_of_secondary_signatories,
            signature,

    ):
        self.set_gen_block_header(block_header=block_header)
        self.set_secondary_signatories(list_of_secondary_signatories=list_of_secondary_signatories)
        self.set_signature(signature=signature)

    def set_before_compete(
            self,
            hash_of_protocol,
            tats: dict,
            dict_of_bcws,
            pubkey_dict,

    ):
        self.set_validity_protocol(hash_of_protocol=hash_of_protocol)
        self.set_tats(tats=tats)
        self.set_bcws(dict_of_bcws=dict_of_bcws)
        self.set_gen_pub_key(pubkey_dict=pubkey_dict)

    def set_gen_block_header(self, block_header: GenesisBlockHeader):

        self.bh = block_header

    def set_validity_protocol(self, hash_of_protocol):

        self.vph = hash_of_protocol

    def set_tats(self, tats: dict):

        self.tats = tats

    def set_bcws(self, dict_of_bcws):

        self.bcws = dict_of_bcws

    def set_secondary_signatories(self, list_of_secondary_signatories):

        self.s_s = list_of_secondary_signatories

    def set_gen_pub_key(self, pubkey_dict):
        self.pubkey = pubkey_dict

    def set_signature(self, signature):

        self.sig = signature


class NonGenesisBlock(BaseBlock):

    def __init__(self):
        super().__init__()
        self.tx = None
        self.misc_msgs = None
        self.wsh = None

    def set_block_header(self, block_header):
        self.bh = block_header

    def set_txs(self, transaction_dict: dict):
        self.tx = transaction_dict

    def set_misc_msgs(self, misc_msgs: dict):
        self.misc_msgs =  misc_msgs

    def set_wsh_dict(self, wsh):
        self.wsh = wsh

    def set_before_competing(self, transaction_dict, misc_msgs, wsh):
        self.set_txs(transaction_dict=transaction_dict)
        self.set_misc_msgs(misc_msgs=misc_msgs)
        self.set_wsh_dict(wsh=wsh)


class BlockOne(NonGenesisBlock):

    def set_signatories_of_gen_block(self, signatories_list: list):
        self.misc_msgs["gen_s_s"] = signatories_list




class RegularBlock(NonGenesisBlock):
    pass

if __name__ == '__main__':
    pass