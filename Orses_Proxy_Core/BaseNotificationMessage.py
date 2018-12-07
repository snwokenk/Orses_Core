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
import json, time
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Crypto.Hash import SHA256


class BaseNotificationMessage:
    def __init__(self, proxy_center, type_of_msg, msg_snd, msg_rcv, msg, value: int, type_of_value, value_sender='sndr'):
        """

        :param proxy_center: instance of proxy_center
        :param type_of_msg: type of message executed an being notified ie if BTR executed then type is 'btr'
        :param msg_snd: wallet id (either a BCW or regular wallet) that sent message (directly or through proxy)
        :param msg_rcv: wallet id (either a BCW or regular wallet) that receive message (directly or through proxy)
        :param msg: msg relating to notification ie BTC asgn_stmt
        """
        self.msg_rcv = msg_rcv
        self.msg_snd = msg_snd
        self.proxy_center = proxy_center
        self.msg = msg
        self.hash_of_msg = msg["tx_hash"] if "tx_hash" in msg else (msg["stmt_hsh"] if "stmt_hsh" in msg else None)
        self.type_of_msg = type_of_msg
        self.value = value
        self.value_sndr = value_sender
        self.type_of_value = type_of_value  # 'payable', 'reserved' etc
        self.admin_inst = self.proxy_center.admin_inst

    def get_sender_wid(self):
        # Override
        pass

    def create_notif_msg(self):
        if self.hash_of_msg:
            notif_msg = [self.type_of_msg, self.hash_of_msg, self.msg_snd, self.msg_rcv, self.admin_inst.admin_id,
                         f"{self.value}|{self.type_of_value}|{self.value_sndr}"]
            return notif_msg

    def sign_and_return_notif_msg(self, bcw_proxy_privkey):
        """

        :param bcw_proxy_privkey: the privkey associated with the proxy-bcw
        :return: dict of notif msg
        """

        main_notif_msg = self.create_notif_msg()

        if bcw_proxy_privkey and main_notif_msg:


            signature = DigitalSigner.sign_with_provided_privkey(
                dict_of_privkey_numbers=None,
                message=main_notif_msg[1],  # hash of msg notif is based on ie if btr then hash of BTR
                key=bcw_proxy_privkey
            )
            main_notif_msg.append(signature)
            notif_msg_json = json.dumps(main_notif_msg)

            tx_hash = SHA256.new(notif_msg_json.encode()).hexdigest()

            notif_dict = {
                "time": int(time.time()),
                "tx_hash": tx_hash,  # hash of notif message
            }


            return notif_dict, main_notif_msg
        else:
            return {}, {}



