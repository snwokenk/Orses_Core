from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator

import time

class MiscMessagesValidator:
    def __init__(self, misc_msg_dict, admin_instance,  price_per_byte=0.00001, timelimit=300,  q_object=None):
        self.admin_instance = admin_instance
        self.q_object = q_object
        self.price_per_byte = price_per_byte
        self.misc_msg_dict = misc_msg_dict
        self.msg_hash = misc_msg_dict["msg_hash"]
        self.msg = misc_msg_dict["msg"]
        self.sig = misc_msg_dict["sig"]
        self.wallet_pubkey = misc_msg_dict["pubkey"]
        self.msg_purpose = misc_msg_dict["purp"]
        self.msg_fee = misc_msg_dict["fee"]
        self.timestamp = misc_msg_dict["time"]
        self.curr_time = time.time()
        self.msg_size = self.calc_msg_size()
        self.msg_minimum_cost = self.calc_msg_size()
        self.msg_fee_enough = self.check_if_msg_fee_is_enough()

    def calc_minimum_msg_cost(self):
        return round(self.msg_size * self.price_per_byte, 10)

    def calc_msg_size(self, pubkey_key_size=100):

        size_of_msg = len(self.msg)
        return size_of_msg + pubkey_key_size

    def check_validity(self):
        """
        For misc message, if token ownership not in form of transfer transaction but rather in form of
        assignment statements, proxies of BCWs will have to be queried. THis will cause a blocking code,
        therefore if that is necessary then a deferral might be used or it is run in a separated thread
        :return:
        """
        if self.check_if_wallet_has_enough_tokens():
            self.q_object([f'b{self.msg_hash[:8]}', self.wallet_pubkey, self.misc_msg_dict, True])
        else:
            self.q_object([f'b{self.msg_hash[:8]}', self.wallet_pubkey, self.misc_msg_dict, False])

    def check_if_msg_fee_is_enough(self):

        return self.msg_fee >= self.msg_minimum_cost

    def check_if_wallet_has_enough_tokens(self):

        if self.msg_fee_enough:
            return True  # todo: this will check the blockchain to verify enough token in wallet




