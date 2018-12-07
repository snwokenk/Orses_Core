from Orses_Proxy_Core.BaseNotificationMessage import BaseNotificationMessage


class ExecutedAsgnStmtNotifMsg(BaseNotificationMessage):

    def __init__(self, proxy_center, msg_snd, msg_rcv, msg, value, bcw_proxy_pubkey,
                 type_of_msg="ex_asgn_notif", value_sender="sndr"):
        """

        :param proxy_center:
        :param msg_snd: wallet id of wallet sending asgn stmt
        :param msg_rcv: wallet id of wallet receiving asgn stmt
        :param msg:
        :param value:
        :param value_sender: value sender will always be the message sender in asgn stmt
        :param bcw_proxy_pubkey:
        :param type_of_msg:
        """

        self.bcw_proxy_pubkey = bcw_proxy_pubkey
        self.type_of_value = "available"
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

    def sign_and_return_executed_asgn_stmt_notif(self, bcw_proxy_privkey):

        if not self.notif_msg:
            exec_asgn_dict, main_dict = self.sign_and_return_notif_msg(bcw_proxy_privkey=bcw_proxy_privkey)

            if exec_asgn_dict:

                exec_asgn_dict["notif_msg"] = main_dict
                exec_asgn_dict["bcw_proxy_pubkey"] = self.bcw_proxy_pubkey

                self.notif_msg = exec_asgn_dict

                return exec_asgn_dict
        else:
            return self.notif_msg

        return None