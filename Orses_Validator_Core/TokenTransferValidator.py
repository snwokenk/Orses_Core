from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Database_Core import RetrieveData, StoreData
import time, json


class TokenTransferValidator:
    def __init__(self, transfer_tx_dict, wallet_pubkey=None,  timelimit=300):
        self.transfer_tx_dict_json = json.dumps(transfer_tx_dict["ttx"])
        self.sending_wallet_pubkey = wallet_pubkey
        self.sending_wid = transfer_tx_dict["ttx"]["snd_wid"]
        self.sending_client_id = transfer_tx_dict["client_id"]
        self.receiving_wid = transfer_tx_dict["ttx"]["rcv_wid"]
        self.signature = transfer_tx_dict["sig"]
        self.tx_hash = transfer_tx_dict["tx_hash"]
        self.timestamp = transfer_tx_dict["ttx"]["time"]
        self.amt = transfer_tx_dict["ttx"]["amt"]
        self.fee = transfer_tx_dict["ttx"]["fee"]
        self.timelimit = timelimit
        self.unknown_wallet = True if wallet_pubkey else False
        self.set_sending_wallet_pubkey()

    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.sending_wallet_pubkey is None:
            snd_wid = self.sending_wid

            self.sending_wallet_pubkey = RetrieveData.RetrieveData.get_pubkey_of_wallet(wid=snd_wid)
            # print(len(snd_wid))
            # print("sending pubkey: ", self.sending_wallet_pubkey)

    def check_validity(self):
        if self.sending_wallet_pubkey == "":
            return None
        elif (self.check_client_id_owner_of_wallet(),
                self.check_signature_valid(),
                self.check_timestamp()):
            if self.unknown_wallet:
                StoreData.StoreData.store_wallet_info_in_db(
                    wallet_id=self.sending_wid,
                    wallet_owner=self.sending_client_id,
                    wallet_pubkey=self.sending_wallet_pubkey
                )

            StoreData.StoreData.store_token_transfer_tx_info_in_db(
                amt=self.amt,
                fee=self.fee,
                snd_wid=self.sending_wid,
                rcv_wid=self.receiving_wid,
                time=self.timestamp,
                sig=self.signature,
                json_ttx_dict=self.transfer_tx_dict_json,
                tx_hash=self.tx_hash


            )
            return True
        else:
            return False

    def check_client_id_owner_of_wallet(self):
        step1 = SHA256.new(self.sending_wallet_pubkey + self.sending_client_id.encode()).digest()
        derived_wid = "W" + RIPEMD160.new(step1).hexdigest()

        print("owner check: ", derived_wid == self.sending_wid)

        return derived_wid == self.sending_wid

    def check_signature_valid(self):
        response = DigitalSignerValidator.validate_wallet_signature(msg=self.transfer_tx_dict_json,
                                                                    wallet_pubkey=self.sending_wallet_pubkey,
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
            if amt > 0.0 and fee > 0.0: # verify amt and fee is not negative
                print("inputs Check: ", True)
                return True
            else:
                print("inputs Check: ", False)
                return False