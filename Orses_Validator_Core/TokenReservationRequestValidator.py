from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Database_Core import RetrieveData, StoreData
import time, json


# Todo: complete validator class, after checking validity store in db for token reservation
class TokenReservationRequestValidator:

    def __init__(self, tkn_rsv_dict, wallet_pubkey=None, q_object=None):
        self.tkn_rsv_dict = tkn_rsv_dict
        self.rsv_req_json = json.dumps(tkn_rsv_dict["rsv_req"])
        self.amount = tkn_rsv_dict["rsv_req"]["amt"]
        self.fee = tkn_rsv_dict["rsv_req"]["fee"]
        self.timestamp = tkn_rsv_dict["rsv_req"]["time"]
        self.resevation_expiration = tkn_rsv_dict["rsv_req"]["exp"]
        self.wallet_pubkey = wallet_pubkey
        self.client_id = tkn_rsv_dict["client_id"]
        self.wallet_id = tkn_rsv_dict["rsv_req"]["req_wid"]
        self.signature = tkn_rsv_dict["sig"]
        self.tx_hash = tkn_rsv_dict["tx_hash"]
        self.q_object = q_object

        self.unknown_wallet = True if wallet_pubkey else False

        self.set_sending_wallet_pubkey()

    def check_validity(self):
        if self.wallet_pubkey == "":
            return None

        elif (self.check_client_id_owner_of_wallet(),
              self.check_signature_valid(),
              self.check_inputs(),
              self.check_minimum_time(),
              self.check_if_wallet_has_enough_token()
              ):
            if self.unknown_wallet:
                StoreData.StoreData.store_wallet_info_in_db(
                    wallet_id=self.wallet_id,
                    wallet_owner=self.client_id,
                    wallet_pubkey=self.wallet_pubkey
                )
            StoreData.StoreData.store_token_rsv_req_info_in_db(
                tx_hash=self.tx_hash,
                wid=self.wallet_id,
                amt=float(self.amount),
                fee=float(self.fee),
                timestamp=int(self.timestamp),
                expiration=int(self.resevation_expiration),
                owner_id=self.client_id,
                sig=self.signature,
                json_trr_dict=self.rsv_req_json

            )

            # pass validated message to network propagator and competing process(if active)
            # 'c' reason message for token reservation request msg
            if self.q_object:
                self.q_object.put([f'c{self.tx_hash[:8]}', self.wallet_pubkey.hex(), self.tkn_rsv_dict, True])
            return True
        else:
            if self.q_object:
                self.q_object.put([f'c{self.tx_hash[:8]}', self.wallet_pubkey.hex(), self.tkn_rsv_dict, False])
            return False

    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.wallet_pubkey is None:
            snd_wid = self.wallet_id

            self.wallet_pubkey = RetrieveData.RetrieveData.get_pubkey_of_wallet(wid=snd_wid)
            # print(len(snd_wid))
            # print("sending pubkey: ", self.sending_wallet_pubkey)

    def check_client_id_owner_of_wallet(self):
        step1 = SHA256.new(self.wallet_pubkey + self.client_id.encode()).digest()
        derived_wid = "W" + RIPEMD160.new(step1).hexdigest()

        print("owner check: ", derived_wid == self.wallet_id)

        return derived_wid == self.wallet_id

    def check_signature_valid(self):
        response = DigitalSignerValidator.validate_wallet_signature(msg=self.rsv_req_json,
                                                                    wallet_pubkey=self.wallet_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

    def check_if_wallet_has_enough_token(self):
        """
        reservation request must be to reserve at least 250000, fee to reserve is 1 token
        :return: bool, true if amount being reserved and wallet balance is at least 250001
        """

        # TODO: this should look at blockchain and determine if wallet has enough tokens for now return true

        return True

    def check_minimum_time(self):
        """
        tokens must be reserved for at least 30*86400 seconds. Reservation could be revoked after 1/4 time has passed
        minimum reservation time = 2592000 seconds
        minimum time until ability to revoke = 648000 seconds (7.5 days)
        :return:
        """
        if not int(time.time()) < int(self.timestamp + 300):  # first verify request not stale
            return False
        return (self.resevation_expiration - self.timestamp) >= 2592000  # 30 days in seconds

    def check_inputs(self):
        try:
            amt = float(self.amount)
            fee = float(self.fee)
        except ValueError:
            print("inputs Check: ", False)
            return False
        else:
            if amt >= 250000.00 and fee >= 1.00: # verify amt and fee is not negative
                print("inputs Check: ", True)
                return True
            else:
                print("inputs Check: ", False)
                return False

