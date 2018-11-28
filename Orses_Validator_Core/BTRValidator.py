from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Database_Core import RetrieveData, StoreData
from Orses_Validator_Core.BaseProxyMessageValidator import BaseProxyMessageValidator
from Orses_Proxy_Core.BTRNotificationMessage import BTRNotificationMessage
from Orses_Util_Core.OrsesTokenMath import OrsesTokenMath


import time, json


# todo: change certain names to make it clear the bcw sending the BTR vs BCW required to send value (two different)

class BTRValidator(BaseProxyMessageValidator):
    """
    BTR validates a Balance Transfer Request
    Balance transfer requests do not go on the blockchain but are exchanged and stored by BCWs.
    They go under BCW activities which is used to derived the Merkle Root for a BCW's wallet hash state
    """

    def __init__(self, btr_dict, proxy_center, wallet_pubkey=None, time_limit=300, q_object=None, asgn_validated=False,
                 send_network_notif=False):

        self.proxy_center = proxy_center
        self.admin_instance = proxy_center.admin_inst
        self.send_network_notif = send_network_notif
        self.btr_dict = btr_dict
        self.btr = btr_dict['btr']

        # self.snd_admin_id required by Baseclass
        self.snd_admin_id = btr_dict["admin_id"]

        self.signature = btr_dict["sig"]

        # required by validate_asgn_stmt() method in base class
        self.asgn_sender_pubkey = btr_dict["a_snd_pk"]
        self.btt_hash = btr_dict['tx_hash']
        self.related_asgn_stmt_dict = self.btr['asgn_stmt']

        # related_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
        self.related_asgn_stmt_list = self.related_asgn_stmt_dict['asgn_stmt'].split(sep='|')

        self.amt = OrsesTokenMath.convert_orses_tokens_to_ntakiris(self.related_asgn_stmt_list[3])
        self.fee = OrsesTokenMath.convert_orses_tokens_to_ntakiris(self.related_asgn_stmt_list[4])
        # self.value = float(self.related_asgn_stmt_list[3]) + self.related_asgn_stmt_list[4]
        self.value = self.amt + self.fee

        # bcw wid requesting to receive value Required by base class
        self.bcw_wid = self.related_asgn_stmt_list[2]

        # BCW meant to sent value to requesting bcw
        self.transferring_bcw = self.btr['snd_bcw']



        self.managed_wallet = self.related_asgn_stmt_list[0]  # wallet which sent the assignment statment

        self.main_dict_json = json.dumps(self.btr)

        self.btr_fee = 0  # no fee, this request is send between proxy nodes

        # call init of BaseClass
        super().__init__(
            admin_instance=self.admin_instance,
            wallet_pubkey=wallet_pubkey,
            time_limit=time_limit,
            q_object=q_object,
            asgn_validated=asgn_validated
        )

        # inherited from Baseclass
        self.set_sending_wallet_pubkey()

        # wallet proxy

        self.wallet_proxy = self.admin_instance.proxy_center.dict_of_managing_bcw.get(
            self.bcw_wid if asgn_validated is True else self.transferring_bcw,
            None
        )
        self.btr_notif_msg: dict = None

    def get_wallet_proxy_of_bcw(self, bcw_wid):
        """
        used to get wallet proxy of receiving bcw(IF and ONLY IF a receiving BCW is managed by local node)
        :return:
        """
        wallet_proxy = self.proxy_center.get_a_proxy(bcw_wid=bcw_wid)
        return wallet_proxy

    def get_wallet_proxy_pubkey(self,bcw_wid):

        wallet_proxy = self.get_wallet_proxy_of_bcw(bcw_wid=bcw_wid)
        if wallet_proxy:
            return wallet_proxy.get_pubkey()
        else:
            return {}

    def get_wallet_proxy_privkey(self, bcw_wid):

        wallet_proxy = self.get_wallet_proxy_of_bcw(bcw_wid=bcw_wid)

        if wallet_proxy:
            return wallet_proxy.g

        else:
            return {}

    def check_validity(self):
        if not self.non_json_proxy_pubkey:  # if empty dict {}
            return None
        elif self.non_json_proxy_pubkey is False:
            return False
        elif self.wallet_proxy is None:
            print(f"in BTRValidator.py, self.wallet_proxy is None, returning False")
            return False

        if (self.check_node_is_valid_proxy() and self.check_signature_valid() and self.check_both_bcw_valid() and
                self.validate_asgn_stmt()):

            # todo: allow for insertion in wallet proxy db (by receiver of BTR
            # todo: this can be done by passing a callable which does all the additions, subtractions and insertions
            # todo: send notification message
            if self.send_network_notif is True:
                self.btr_notif_msg = BTRNotificationMessage(
                    proxy_center=self.proxy_center,
                    msg_snd=self.bcw_wid,
                    msg_rcv=self.transferring_bcw, # btr is sent to transferring bcw,
                    msg=self.btr_dict,
                    value=self.value,
                    # use self.get_wallet_proxy_of_bcw with self.transferring bcw
                    # bcw_proxy_pubkey of local node creating notif message not
                    bcw_proxy_pubkey=self.get_wallet_proxy_pubkey(bcw_wid=self.transferring_bcw)

                )
                notif_msg = self.btr_notif_msg.sign_and_return_balance_transfer_request_notif(
                    bcw_proxy_privkey=self.get_wallet_proxy_privkey(bcw_wid=self.transferring_bcw)

                )
                if notif_msg:

                    self.q_object.put(
                        [
                            f'g{notif_msg["tx_hash"][:8]}',
                            self.get_wallet_proxy_pubkey(bcw_wid=self.transferring_bcw),
                            notif_msg,
                            True
                        ]
                    )
                else:
                    print(f"in BTRVALIDATOR.py, NOT ABLE TO SEND NOTIFICATION MESSAGE TO NETWORK")

            return True
        else:
            return False

    def check_both_bcw_valid(self):

        if (self.db_manager.get_from_bcw_db(wallet_id=self.bcw_wid) and
                self.db_manager.get_from_bcw_db(wallet_id=self.transferring_bcw)):
            return True
        else:
            return False





