from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Database_Core import RetrieveData, StoreData

import time, json


class BTTValidator:

    def __init__(self, btt_dict, admin_instance, bcw_proxy_pubkey=None,  timelimit=300, q_object=None):

        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
        self.db_manager = self.admin_instance.get_db_manager()
        self.bcw_proxy_pubkey = bcw_proxy_pubkey
        self.non_json_proxy_pubkey = None
        self.btt_dict = btt_dict
        self.btt = btt_dict['btt']
        self.snd_admin_id =btt_dict["admin_id"]
        self.btt_hash = btt_dict['tx_hash']
        self.related_asgn_stmt_dict = self.btt['asgn_stmt']

        # [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
        self.related_asgn_stmt_list = self.related_asgn_stmt_dict['asgn_stmt'].split(sep='|')
        self.btt_dict_json = json.dumps(self.btt)
        self.timelimit = timelimit
        self.q_object = q_object

        self.set_sending_wallet_pubkey()

    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.bcw_proxy_pubkey is None:

            # proxy id, is just bcw_wid+proxy's admin id
            bcw_proxy_id = f"{self.related_asgn_stmt_list[2]}{self.snd_admin_id}"

            self.bcw_proxy_pubkey = RetrieveData.RetrieveData.get_pubkey_of_wallet(
                wid=snd_wid,
                user_instance=self.admin_instance
            )
            self.non_json_proxy_pubkey = None if not self.bcw_proxy_pubkey else \
                json.loads(self.bcw_proxy_pubkey)
            # print(len(snd_wid))
            # print("sending pubkey: ", self.sending_wallet_pubkey)
        else:
            try:
                self.non_json_proxy_pubkey = json.loads(self.bcw_proxy_pubkey)
            except TypeError as e:
                if isinstance(self.bcw_proxy_pubkey, dict):  # already a python object
                    self.non_json_proxy_pubkey = self.bcw_proxy_pubkey
                else:
                    self.non_json_proxy_pubkey = False

    def check_validity(self):
        if self.non_json_proxy_pubkey is None:
            return None
        elif self.non_json_proxy_pubkey is False:
            return False

        if self.check_signature_valid() is True:

            # send btt to NetworkPropagator.run_propagator_convo_initiator
            self.q_object.put([f'e{self.btt_hash[:8]}', wallet_proxy.bcw_proxy_pubkey, self.btt_dict, True])
            return True
        else:
            return False


    def check_signature_valid(self):
        response = DigitalSignerValidator.validate_wallet_signature(msg=self.btt_dict_json,
                                                                    wallet_pubkey=self.non_json_wallet_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

