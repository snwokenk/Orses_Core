from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Database_Core import RetrieveData, StoreData
import time, json


class TokenReservationRevokeValidator:
    def __init__(self, tkn_rvk_dict, wallet_pubkey=None, q_object=None):
        self.tkn_rvk_dict = tkn_rvk_dict
        self.wallet_pubkey = wallet_pubkey
        self.rvk_req_json = json.dumps(tkn_rvk_dict["rvk_req"])
        self.fee = tkn_rvk_dict["rvk_req"]["fee"]
        self.timestamp = tkn_rvk_dict["rvk_req"]["time"]
        self.client_id = tkn_rvk_dict["client_id"]
        self.wallet_id = tkn_rvk_dict["rvk_req"]["req_wid"]
        self.signature = tkn_rvk_dict["sig"]
        self.tx_hash = tkn_rvk_dict["tx_hash"]
        self.trr_tx_hash = tkn_rvk_dict["rvk_req"]["trr_hash"]
        self.q_object = q_object

        self.unknown_wallet = True if wallet_pubkey else False

        self.set_sending_wallet_pubkey()

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

    def check_validity(self):
        if self.wallet_pubkey == "":
            return None

        elif (self.check_client_id_owner_of_wallet(),
                self.check_signature_valid(),
                self.check_reservation_meets_minimum_time()):
            if self.unknown_wallet:
                StoreData.StoreData.store_wallet_info_in_db(
                    wallet_id=self.wallet_id,
                    wallet_owner=self.client_id,
                    wallet_pubkey=self.wallet_pubkey
                )
            StoreData.StoreData.store_token_revoke_req_in_db(
                tx_hash=self.tx_hash,
                trr_hash=self.trr_tx_hash,
                wid=self.wallet_id,
                fee=float(self.fee),
                timestamp=int(self.timestamp),
                owner_id=self.client_id,
                sig=self.signature,
                json_trx_dict=self.rvk_req_json

            )

            # pass validated message to network propagator and competing process(if active)
            # 'd' reason message for token reservation revoke msg
            if self.q_object:
                self.q_object.put(['d', self.tx_hash,  self.wallet_pubkey, self.tkn_rvk_dict])

            return True
        else:
            return False

    def check_client_id_owner_of_wallet(self):
        step1 = SHA256.new(self.wallet_pubkey + self.client_id.encode()).digest()
        derived_wid = "W" + RIPEMD160.new(step1).hexdigest()

        print("owner check: ", derived_wid == self.wallet_id)

        return derived_wid == self.wallet_id

    def check_signature_valid(self):
        response = DigitalSignerValidator.validate_wallet_signature(msg=self.rvk_req_json,
                                                                    wallet_pubkey=self.wallet_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

    def check_reservation_meets_minimum_time(self):

        # TODO: Because blockchain not open, use this, but once blockchain running, this will be a function
        # todo: to query the blockchain and look for token reservation request with hash
        trr_dict = RetrieveData.RetrieveData.get_token_reservation_requests(tx_hash=self.trr_tx_hash)
        print("trr_hash: ", self.trr_tx_hash)

        if self.trr_tx_hash in trr_dict:
            trr = trr_dict[self.trr_tx_hash][1]
            exp = trr["exp"]
            time1 = trr["time"]
            duration = exp - time1
            if duration > 0:
                min_timestamp = time1 + int(duration/4)
                min_time = int(time.time()) >= min_timestamp
                print("minimum rsv time met: ", min_time)
                return min_time

        else:
            return False


