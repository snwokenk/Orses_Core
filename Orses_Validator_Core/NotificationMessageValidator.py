"""
Used to validate Notification messages

Notification messages are dicts with:
{
'notif_msg': main notif message list
'bcw_proxy_pubkey': pubkey used by proxy to uniquely identify activities done on behalf of BCW
'time': time of notification message creation
'tx_hash' hash of json encoded main notif message list
}


main notif message list:
type of msg ie btr executed, msg executed's hash, sender of msg, receiver of msg, proxy admin id,
str "value|type(payable, reserved available etc)|(receiver of value sndr or rcvr))", base85 sig using msg hash]

example: ['btr', 'ff77565d6fd', 'Wf785', 'w901ab', 'VID-1234abcd', "100|payable|sndr", 'sdfjhdfkjh1y9378']
"""

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator

class NotificationMessageValidator:
    def __init__(self, notif_msg_dict, admin_instance, wallet_pubkey=None,  timelimit=300, q_object=None):
        """

        :param notif_msg_dict: the main notificaiton dict
        :param admin_instance: admin instance
        :param wallet_pubkey: Not used just done to provide compatibility
        :param timelimit:
        :param q_object:
        """

        self.admin_instance = admin_instance
        self.db_manager = admin_instance.get_db_manager()
        self.notif_msg_dict = notif_msg_dict
        self.q_object = q_object
        self.main_notif_list: list = notif_msg_dict['notif_msg']
        self.value, self.type_of_value, self.value_sender = self.main_notif_list[5].split('|')
        self.sending_bcw = notif_msg_dict['snd_bcw']
        self.admin_id_of_proxy = notif_msg_dict["admin_id"]
        self.bcw_proxy_pubkey = None
        self.type_of_msg = self.main_notif_list[0]

        # hash of message being notified about. if notif is about asgn stmt then the asgn stmt hash is provided
        # this hash is used to create signature therefore used to validate signature
        self.hash_of_msg_notified = self.main_notif_list[1]
        self.signature = self.main_notif_list[6]

        self.set_sending_bcw_proxy_pubkey()

    def set_sending_bcw_proxy_pubkey(self):
        # proxy id, is just bcw_wid+proxy's admin id
        # self.bcw_wid and self.snd_admin_id should be found in inherited class
        bcw_proxy_id = f"{self.sending_bcw}{self.admin_id_of_proxy}"

        self.bcw_proxy_pubkey = self.db_manager.get_proxy_pubkey(proxy_id=bcw_proxy_id)

    def check_validity(self):
        """
        To be valid,
        1
        check signature of proxy sending notif message, hash of original message(ie asgn stmt, BTR etc) is used for the
        signature and not the hash of the notif message

        2
        verify admin node is a valid proxy node of related BCW

        3
        verify signature of original message sender (if asgn_stmt then signature of sending wallet)

        :return:
        """

        if self.check_node_is_valid_proxy() and self.check_signature_of_notif_sender():
            pass

    def check_signature_of_notif_sender(self):
        if self.bcw_proxy_pubkey is None:
            return False

        response = DigitalSignerValidator.validate_wallet_signature(msg=self.hash_of_msg_notified,
                                                                    wallet_pubkey=self.bcw_proxy_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False


    def check_node_is_valid_proxy(self):
        """
        logic that checks that the sending Node is a valid proxy for the BCW used in the assignment statement
        :return:
        """

        bcw_info = self.db_manager.get_from_bcw_db(
            wallet_id=self.sending_bcw
        )

        if isinstance(bcw_info, list) and len(bcw_info) > 4:
            return self.admin_id_of_proxy in bcw_info[4]
        else:
            return False



