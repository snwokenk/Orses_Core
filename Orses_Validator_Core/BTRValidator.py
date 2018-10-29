from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Database_Core import RetrieveData, StoreData
from Orses_Validator_Core.BaseProxyMessageValidator import BaseProxyMessageValidator


import time, json


class BTRValidator(BaseProxyMessageValidator):
    """
    BTR validates a Balance Transfer Request
    """

    def __init__(self, btr_dict, admin_instance, wallet_pubkey=None, time_limit=300, q_object=None):


        self.btr_dict = btr_dict
        self.btr = btr_dict['btr']

        # self.snd_admin_id required by Baseclass
        self.snd_admin_id = btr_dict["admin_id"]

        self.signature = btr_dict["sig"]
        self.btt_hash = btr_dict['tx_hash']
        self.related_asgn_stmt_dict = self.btr['asgn_stmt']

        # related_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
        self.related_asgn_stmt_list = self.related_asgn_stmt_dict['asgn_stmt'].split(sep='|')

        # bcw wid Required by base class
        self.bcw_wid = self.related_asgn_stmt_list[2]

        self.managed_wallet = self.related_asgn_stmt_list[0]

        self.main_dict_json = json.dumps(self.btr)

        self.btt_fee = 0  # no fee, this request is send between proxy nodes

        # call init of BaseClass
        super().__init__(
            admin_instance=admin_instance,
            wallet_pubkey=wallet_pubkey,
            time_limit=time_limit,
            q_object=q_object
        )

        # inherited from Baseclass
        self.set_sending_wallet_pubkey()

    def check_validity(self):
        if not self.non_json_proxy_pubkey:  # if empty dict {}
            return None
        elif self.non_json_proxy_pubkey is False:
            return False



