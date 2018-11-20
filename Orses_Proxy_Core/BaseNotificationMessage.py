"""

Base Notification Message
A notification message is used by a proxy to notify the network of a transaction executed
notification messages are also sent to senders of certain messages like BTR as proof of completion.
Also, notification messages are sent whenever a proxy executes an assignment statement first to the network and second
to the sendning wallet client

notif message is a list:

[type of msg ie btr executed, msg executed's hash, sender of msg, receiver of msg, proxy admin id,
str "value|type(payable, reserved available etc)|(receiver of value sndr or rcvr))", base85 sig using msg hash]
ie ['btr', 'ff77565d6fd', 'Wf785', 'w901ab', 'VID-1234abcd', "100|payable|sndr", 'sdfjhdfkjh1y9378']
"""


class BaseNotificationMessage:
    def __init__(self, proxy_center, type_of_msg, msg_snd, msg_rcv, msg, value: int, value_sender='sndr'):
        """

        :param proxy_center:
        :param type_of_msg:
        :param msg: msg relating to notification ie BTC asgn_stmt
        """
        self.msg_rcv = msg_rcv
        self.msg_snd = msg_snd
        self.proxy_center = proxy_center
        self.msg = msg
        self.hash_of_msg = msg["tx_hash"] if "tx_hash" in msg else (msg["stmt_hsh"] if "stmt_hsh" in msg else None)
        self.type_of_msg = type_of_msg
        self.admin_inst = self.proxy_center.admin_inst



    def get_sender_wid(self):
        # Override
        pass


    def create_notif_msg(self):

        notif_msg = [self.type_of_msg, self.hash_of_msg, self.msg_snd, self.msg_rcv, self.admin_inst.admin_id]


    def sign_and_return_notif_msg(self, bcw_proxy_privkey):
        pass




