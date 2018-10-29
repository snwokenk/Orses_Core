from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Database_Core import RetrieveData, StoreData


import time, json


class BTRValidator:

    def __init__(self, btr_dict, admin_instance, wallet_pubkey=None,  timelimit=300, q_object=None):

        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
        self.db_manager = self.admin_instance.get_db_manager()

        # to maintain compatibility argument is called wallet_pubkey but should be bcw_proxy_pubkey
        self.bcw_proxy_pubkey = wallet_pubkey
        self.non_json_proxy_pubkey = None
        self.btr_dict = btr_dict
        self.btr = btr_dict['btr']


        self.snd_admin_id =btr_dict["admin_id"]
        self.signature = btr_dict["sig"]
        self.btt_hash = btr_dict['tx_hash']
        self.related_asgn_stmt_dict = self.btr['asgn_stmt']

        # related_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
        self.related_asgn_stmt_list = self.related_asgn_stmt_dict['asgn_stmt'].split(sep='|')

        # bcw wid
        self.bcw_wid = self.related_asgn_stmt_list[2]

        self.managed_wallet = self.related_asgn_stmt_list[0]

        self.btt_dict_json = json.dumps(self.btr)
        self.timelimit = timelimit
        self.q_object = q_object
        self.btt_fee = 0 # no fee, this request is send between proxy nodes

        self.set_sending_wallet_pubkey()


    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.bcw_proxy_pubkey is None:

            # proxy id, is just bcw_wid+proxy's admin id
            bcw_proxy_id = f"{self.bcw_wid}{self.snd_admin_id}"

            self.non_json_proxy_pubkey = self.db_manager.get_proxy_pubkey(proxy_id=bcw_proxy_id)


        else:
            try:
                self.non_json_proxy_pubkey = json.loads(self.bcw_proxy_pubkey)
            except TypeError as e:
                if isinstance(self.bcw_proxy_pubkey, dict):  # already a python object
                    self.non_json_proxy_pubkey = self.bcw_proxy_pubkey
                else:
                    self.non_json_proxy_pubkey = False

