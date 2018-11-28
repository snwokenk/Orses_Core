from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Database_Core import RetrieveData, StoreData
from Orses_Util_Core.OrsesTokenMath import OrsesTokenMath

import time, json


class TokenTransferValidator:
    def __init__(self, transfer_tx_dict, admin_instance, wallet_pubkey=None,  timelimit=300, q_object=None):
        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
        self.db_manager = self.admin_instance.get_db_manager()
        self.transfer_tx_dict = transfer_tx_dict
        self.transfer_tx_dict_json = json.dumps(transfer_tx_dict["ttx"])
        self.sending_wallet_pubkey = wallet_pubkey
        self.non_json_wallet_pubkey = None
        self.sending_wid = transfer_tx_dict["ttx"]["snd_wid"]
        self.sending_client_id = transfer_tx_dict["client_id"]
        self.receiving_wid = transfer_tx_dict["ttx"]["rcv_wid"]
        self.signature = transfer_tx_dict["sig"]
        self.tx_hash = transfer_tx_dict["tx_hash"]
        self.timestamp = transfer_tx_dict["ttx"]["time"]
        self.amt = transfer_tx_dict["ttx"]["amt"]
        # self.ntakiri_amount = int(round(float(self.amt), 10) * 1e10)
        self.ntakiri_amount = OrsesTokenMath.convert_orses_tokens_to_ntakiris(self.amt)
        self.fee = transfer_tx_dict["ttx"]["fee"]
        # self.ntakiri_fee = int(round(float(self.fee), 10) * 1e10)
        self.ntakiri_fee = OrsesTokenMath.convert_orses_tokens_to_ntakiris(self.fee)
        self.timelimit = timelimit
        self.unknown_wallet = True if wallet_pubkey else False
        self.q_object = q_object
        self.set_sending_wallet_pubkey()

    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.sending_wallet_pubkey is None:
            snd_wid = self.sending_wid

            self.sending_wallet_pubkey = RetrieveData.RetrieveData.get_pubkey_of_wallet(
                wid=snd_wid,
                user_instance=self.admin_instance
            )
            self.non_json_wallet_pubkey = None if not self.sending_wallet_pubkey else \
                json.loads(self.sending_wallet_pubkey)
            # print(len(snd_wid))
            # print("sending pubkey: ", self.sending_wallet_pubkey)
        else:
            self.non_json_wallet_pubkey = json.loads(self.sending_wallet_pubkey)

    def check_validity(self):
        if self.sending_wallet_pubkey == "":
            return None
        elif (self.check_wallet_balance() is True and
                self.check_client_id_owner_of_wallet() is True and
                self.check_signature_valid() is True and
                self.check_timestamp() is True):

            # store info into unconfirmed leveldb
            rsp = self.db_manager.insert_into_unconfirmed_db(
                tx_type="ttx",
                sending_wid=self.sending_wid,
                tx_hash=self.tx_hash,
                signature=self.signature,
                main_tx=self.transfer_tx_dict,
                amt=self.ntakiri_amount,
                fee=self.ntakiri_fee,
                rcv_wid=self.receiving_wid
            )
            if rsp is False:
                print(f"in TokenTransferValidator, check_validity, not able to insert ttx into unconfirmed db")

            if self.unknown_wallet:
                StoreData.StoreData.store_wallet_info_in_db(
                    wallet_id=self.sending_wid,
                    wallet_owner=self.sending_client_id,
                    wallet_pubkey=self.sending_wallet_pubkey,
                    user_instance=self.admin_instance
                )

            StoreData.StoreData.store_token_transfer_tx_info_in_db(
                amt=self.amt,
                fee=self.fee,
                snd_wid=self.sending_wid,
                rcv_wid=self.receiving_wid,
                time=self.timestamp,
                sig=self.signature,
                json_ttx_dict=self.transfer_tx_dict_json,
                tx_hash=self.tx_hash,
                user_instance=self.admin_instance


            )

            # pass validated message to network propagator and competing process(if active)
            # 'b' reason message for token transfer msg
            if self.q_object:
                try:
                    self.q_object.put([f'b{self.tx_hash[:8]}', self.sending_wallet_pubkey, self.transfer_tx_dict, True])
                except Exception as e:
                    print("in TokenTransferValidator.py, exception in check_validity: ", e)
            return True
        else:
            if self.q_object:
                self.q_object.put([f'b{self.tx_hash[:8]}', self.sending_wallet_pubkey, self.transfer_tx_dict, False])
            return False

    def check_client_id_owner_of_wallet(self):
        step1 = SHA256.new(
            WalletPKI.generate_key_from_parts(
                x=self.non_json_wallet_pubkey["x"],
                y=self.non_json_wallet_pubkey["y"],
                in_bytes=True
            ) + self.sending_client_id.encode()
        ).digest()

        derived_wid = "W" + RIPEMD160.new(step1).hexdigest()

        print("owner check: ", derived_wid == self.sending_wid)

        return derived_wid == self.sending_wid

    def check_signature_valid(self):
        response = DigitalSignerValidator.validate_wallet_signature(msg=self.transfer_tx_dict_json,
                                                                    wallet_pubkey=self.non_json_wallet_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

    def check_timestamp(self):
        rsp = int(time.time()) < int(self.timestamp + self.timelimit)

        print("time check", rsp)
        return rsp

    def check_inputs(self):
        """
        checks inputs to make sure they of the proper data type ie amount is
        :return: True if inputs are of write data type else False
        """

        try:
            amt = float(self.amt)
            fee = float(self.fee)
        except ValueError:
            print("inputs Check: ", False)
            return False
        else:
            if amt > 0.0 and fee > 0.0:  # verify amt and fee is not negative
                if (round(amt, 10) == amt) and (round(fee, 10) == fee):
                    print("inputs Check: ", True)
                    return True
                else:
                    print("inputs fee and amount are more than 10 decimal places.\n"
                          "Orses native tokens are divisible by a max 10 billion places")

            print("inputs Check: ", False)
            return False

    def check_wallet_balance(self):

        # uses either confirmed balance or unconfirmed whichever is smaller
        bal_to_use = WalletInfo.get_lesser_of_wallet_balance(admin_inst=self.admin_instance, wallet_id=self.sending_wid)

        # will choose the less of the balance
        if self.ntakiri_amount+self.ntakiri_fee <= bal_to_use:
            print(f"in TokenTransferValidator, Balance Validated, amt ntakiris: {self.ntakiri_amount/1e10} Orses Tokens"
                  f"amt fees: {self.ntakiri_fee/1e10}"
                  f"balance being used {bal_to_use/1e10} Orses Tokens, admin {self.admin_instance.admin_name}")
            return True
        else:
            print(f"in TokenTransferValidator, Balance NOT Validated ntakiris: {self.ntakiri_amount/1e10}"
                  f"balance being used {bal_to_use/1e10} Orses Tokens, admin {self.admin_instance.admin_name}")
            return False



