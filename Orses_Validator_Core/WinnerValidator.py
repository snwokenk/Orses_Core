"""
used to getting competitor hashes and validate
"""
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData


class WinnerValidator:
    def __init__(self, current_block_list=BlockChainData.get_current_known_block()):
        self.blockNo_before_recent = current_block_list[0]-1  # the block before this prob and shuffled hex is used
        self.block_before_recent =BlockChainData.get_block(self.blockNo_before_recent)
        self.maximum_hash_probability = None  # the highest probability a hash should be
        self.shuffled_hex_value = None  # a dict with all possible hex characters (0-9, a-f) and their shuffled values
        self.prime_character = None   # expected leading character in hash == shuffled_hex_value[15]
