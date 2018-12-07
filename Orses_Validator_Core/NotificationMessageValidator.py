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
        self.notif_msg_dict = notif_msg_dict
        self.q_object = q_object
        self.main_notif_list = notif_msg_dict['notif_msg']
        self.bcw_proxy_pubkey = notif_msg_dict['bcw_proxy_pubkey']
        self.type_of_msg = self.main_notif_list[0]
        # hash of message being notified about. if notif is about asgn stmt then the asgn stmt hash is provided
        self.hash_of_msg_notified = self.main_notif_list[1]


    def check_validity(self):
        pass



