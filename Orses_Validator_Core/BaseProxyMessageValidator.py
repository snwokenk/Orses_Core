
"""
contains a baseclass in which
"""
import json

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator


class BaseProxyMessageValidator:
    def __init__(self, admin_instance, wallet_pubkey=None, time_limit=300, q_object=None):
        """
        BaseClass for messages originated by ProxyNode for purpose of fulfilling an assignment statement
        :param admin_instance: instance of Admin class of ProxyNode
        :param wallet_pubkey: the wallet pub, when message is originally sent is None but if local Node does
                not have the w
        :param time_limit:
        :param q_object:
        """

        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
        self.db_manager = self.admin_instance.get_db_manager()

        # to maintain compatibility argument is called wallet_pubkey but should be bcw_proxy_pubkey
        self.bcw_proxy_pubkey = wallet_pubkey
        self.non_json_proxy_pubkey = None
        self.timelimit = time_limit
        self.q_object = q_object

    def check_validity(self):
        # override
        pass

    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.bcw_proxy_pubkey is None:

            # proxy id, is just bcw_wid+proxy's admin id
            # self.bcw_wid and self.snd_admin_id should be found in inherited class
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
        else:
            return False

    def check_signature_valid(self):

        response = DigitalSignerValidator.validate_wallet_signature(msg=self.main_dict_json,
                                                                    wallet_pubkey=self.non_json_proxy_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

