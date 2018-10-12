from Crypto.Hash import SHA256, RIPEMD160
import hashlib
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator

import time, json


# insert tx into unconfirmed, with amt as zero and fee as fee

class MiscMessagesValidator:
    """
    misc_msg_dict =
    {
    'msg_hash': msg hash
    'wid': wallet id
    'misc_msg': {'msg':main msg, 'purp': purpose of message, 'time': timestamp, 'fee': fee (in ORST) }
    'wallet_pupkey' main message
    'sig'  signature using msg_hash

    }

    Note if fee == 0 or less then the msg_minimum_fee is used by the default 0.00001 token per byte, this can be changed
    by each node
    """
    def __init__(self, misc_msg_dict, admin_instance,  price_per_byte=0.00001, wallet_pubkey=None,timelimit=300,  q_object=None):
        self.admin_instance = admin_instance
        self.db_manager = self.admin_instance.get_db_manager()
        self.q_object = q_object
        self.price_per_byte = price_per_byte
        self.misc_msg_dict = misc_msg_dict
        self.main_msg = misc_msg_dict["misc_msg"]
        self.msg_hash = misc_msg_dict["msg_hash"]
        self.wallet_id = misc_msg_dict["wid"]
        self.msg = self.main_msg["msg"]
        self.sig = misc_msg_dict["sig"]
        self.wallet_pubkey = misc_msg_dict["pk"]
        self.msg_purpose = self.main_msg["purp"]
        self.timestamp = self.main_msg["time"]
        self.curr_time = time.time()
        self.msg_size = self.calc_msg_size()
        self.msg_minimum_cost = self.calc_minimum_msg_cost()
        self.msg_fee = int(round(float(self.main_msg["fee"]), 10)*1e10) if int(self.main_msg["fee"]) > 0 else \
            self.msg_minimum_cost

    def calc_minimum_msg_cost(self):
        """
        Messgage cost returned as ntakiriis 1 ORS = 10,000,000,000
        :return:
        """
        return int(round(self.msg_size * self.price_per_byte, 10) * 1e10)

    def calc_msg_size(self, pubkey_key_size=100, hash_size=64, time_size=10, fee_size=10):

        size_of_msg = len(self.msg) + len(self.msg_purpose)
        return size_of_msg + pubkey_key_size + hash_size + time_size + fee_size

    def check_validity(self):
        """
        For misc message, if token ownership not in form of transfer transaction but rather in form of
        assignment statements, proxies of BCWs will have to be queried. THis will cause a blocking code,
        therefore if that is necessary then a deferral might be used or it is run in a separated thread
        :return:
        """
        if self.check_if_msg_fee_is_enough() and self.check_signature():
            # store info into unconfirmed leveldb
            response = self.db_manager.insert_into_unconfirmed_db(
                tx_type="misc_msg",
                sending_wid=self.wallet_id,
                tx_hash=self.msg_hash,
                signature=self.sig,
                main_tx=self.main_msg,
                amt=0,
                fee=self.msg_fee,
            )

            if response is False:
                print(f"in MiscMessageValidator.py, check_validity, not able to insert misc_msg into unconfirmed db")
            if self.q_object:
                self.q_object.put([f'f{self.msg_hash[:8]}', self.wallet_pubkey, self.misc_msg_dict, True])
            return True
        else:
            if self.q_object:
                self.q_object.put([f'f{self.msg_hash[:8]}', self.wallet_pubkey, self.misc_msg_dict, False])
            return False

    def check_signature(self):
        response = DigitalSignerValidator.validate_wallet_signature(
            msg=json.dumps(self.main_msg),
            signature=self.sig,
            wallet_pubkey=self.wallet_pubkey

        )

        print("sig response in MiscValidator: ", response)

        return response

    def check_if_msg_fee_is_enough(self):
        """
        Checks to verify message fee is enough and if wallet has enough tokens
        :return:
        """
        if self.msg_fee >= self.msg_minimum_cost:
            available_bal = WalletInfo.get_lesser_of_wallet_balance(
                admin_inst=self.admin_instance,
                wallet_id=self.wallet_id
            )

            enough_bal = self.msg_fee <= int(available_bal)

            print(f"in MiscMsgValidator, enough bal {enough_bal}")

            return enough_bal
        else:
            print(f"in MiscMessageValidator, msg_fee not enough")
            return False





