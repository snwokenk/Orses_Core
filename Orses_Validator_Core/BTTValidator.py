from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Database_Core import RetrieveData, StoreData

import time, json


class BTTValidator:

    def __init__(self, btt_dict, admin_instance, wallet_pubkey=None,  timelimit=300, q_object=None):

        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
        self.db_manager = self.admin_instance.get_db_manager()

        # to maintain compatibility argument is called wallet_pubkey but should be bcw_proxy_pubkey
        self.bcw_proxy_pubkey = wallet_pubkey
        self.non_json_proxy_pubkey = None
        self.btt_dict = btt_dict
        self.btt = btt_dict['btt']
        self.snd_admin_id =btt_dict["admin_id"]
        self.signature = btt_dict["sig"]
        self.btt_hash = btt_dict['tx_hash']
        self.related_asgn_stmt_dict = self.btt['asgn_stmt']

        # related_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
        self.related_asgn_stmt_list = self.related_asgn_stmt_dict['asgn_stmt'].split(sep='|')

        # bcw wid
        self.bcw_wid = self.related_asgn_stmt_list[2]

        self.asgn_stmt_sndr = self.related_asgn_stmt_list[0]
        self.btt_dict_json = json.dumps(self.btt)
        self.timelimit = timelimit
        self.q_object = q_object
        self.btt_fee = self.btt["fee"]

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

    def check_validity(self):
        if not self.non_json_proxy_pubkey:  # if empty dict {}
            return None
        elif self.non_json_proxy_pubkey is False:
            return False

        if self.check_signature_valid() is True and self.check_node_is_valid_proxy():


            # refactor this, to allow for inclusion into wallet of sender and BCW_WID wallet
            # sending_wid is the BCW and receiving id is the asgn stmt senders wid
            rsp = self.db_manager.insert_into_unconfirmed_db(
                tx_type="btt",
                sending_wid=self.bcw_wid,
                tx_hash=self.btt_hash,
                signature=self.signature,
                main_tx=self.btt_dict,
                amt=0.0,
                fee=self.btt_fee,
                rcv_wid=self.asgn_stmt_sndr
            )

            # send btt to NetworkPropagator.run_propagator_convo_initiator
            self.q_object.put([f'e{self.btt_hash[:8]}', json.dumps(self.non_json_proxy_pubkey), self.btt_dict, True])
            return True
        else:
            self.q_object.put([f'e{self.btt_hash[:8]}', json.dumps(self.non_json_proxy_pubkey), self.btt_dict, False])
            return False

    def check_signature_valid(self):

        response = DigitalSignerValidator.validate_wallet_signature(msg=self.btt_dict_json,
                                                                    wallet_pubkey=self.non_json_proxy_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

    def check_node_is_valid_proxy(self):
        """
        logic that checks that a node is a valid proxy
        :return:
        """

        bcw_info = self.db_manager.get_from_bcw_db(
            wallet_id=self.bcw_wid
        )

        if isinstance(bcw_info, list) and len(bcw_info) > 4:
            return self.snd_admin_id in bcw_info[4]



