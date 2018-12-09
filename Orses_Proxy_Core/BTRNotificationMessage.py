from Orses_Proxy_Core.BaseNotificationMessage import BaseNotificationMessage


class BTRNotificationMessage(BaseNotificationMessage):

    def __init__(self, proxy_center, msg_snd, msg_rcv, msg, bcw_proxy_pubkey, administering_bcw, value: int,
                 value_sender='rcv', type_of_msg='btr_notif'):
        """

        :param proxy_center:
        :param msg_snd: bcw that sent message (btr message NOT notification) ( (the value receiving bcw)
        :param msg_rcv: bcw that received the message (the value transferring BCW)
        :param msg:
        :param bcw_proxy_pubkey: pubkey of proxy representing the transferring bcw
        :param value:
        :param value_sender:
        :param type_of_msg:
        """

        self.administering_bcw = administering_bcw
        self.bcw_proxy_pubkey = bcw_proxy_pubkey
        self.notif_msg = None
        self.type_of_value = 'payable'
        super().__init__(
            proxy_center=proxy_center,
            type_of_msg=type_of_msg,
            msg_snd=msg_snd,
            msg_rcv=msg_rcv,
            msg=msg,
            value=value,
            value_sender=value_sender,
            type_of_value=self.type_of_value
        )

    def sign_and_return_balance_transfer_request_notif(self, bcw_proxy_privkey):
        if not self.notif_msg:
            btr_notif_dict, main_dict = self.sign_and_return_notif_msg(bcw_proxy_privkey=bcw_proxy_privkey)

            if btr_notif_dict:

                btr_notif_dict["notif_msg"] = main_dict
                # btr_notif_dict["bcw_proxy_pubkey"] = self.bcw_proxy_pubkey
                btr_notif_dict["snd_bcw"] = self.administering_bcw
                btr_notif_dict["admin_id"] = self.admin_inst.admin_id

                self.notif_msg = btr_notif_dict

                return btr_notif_dict
        else:
            return self.notif_msg

        return None


