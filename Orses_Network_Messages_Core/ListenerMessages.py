import collections, json

from Orses_Validator_Core import AssignmentStatementValidator, TokenTransferValidator, \
    TokenReservationRequestValidator, TokenReservationRevokeValidator


# add the validator method to the dictionary without calling it without the '()'
validator_dict_callable = dict()
validator_dict_callable["tx_asg"] = AssignmentStatementValidator.AssignmentStatementValidator
validator_dict_callable["tx_ttx"] = TokenTransferValidator.TokenTransferValidator
validator_dict_callable["tx_trr"] = TokenReservationRequestValidator.TokenReservationRequestValidator
validator_dict_callable["tx_trx"] = TokenReservationRevokeValidator.TokenReservationRevokeValidator

retriever_dict_callable = dict()
retriever_dict_callable["rq_adr"] = None
retriever_dict_callable['rq_bal'] = None  # request wallet balance

class ListenerMessages:
    """
    base class, create ListenerMessages subclasses for each type of message.
    These subclasses can then be used in the Network manager depending on the type of connection
    """
    def __init__(self,  messages_heard, netmsginst, msg_type, admin_instance):
        """

        :param messages_heard: a list of messages already heard from client
        :type messages_heard: list

        :param netmsg: the NetworkMessages Instance, instantiating this class. used to access the end_convo of the
        higher class
        :param msg_type: this will be used to determine the validator to call depending on msg type
        """
        assert (isinstance(messages_heard, list)), "first argument of ListenerMessages Class must be a list"

        self.admin_instance = admin_instance
        self.messages_heard = messages_heard
        self.last_msg = b'end'
        self.reject_msg = b'rej'
        self.verified_msg = b'ver'
        self.netmsginst = netmsginst
        self.msg_type = msg_type

    def listen(self, msg):
        """
        used listen to message and then speaks
        :param msg:
        :return:
        """
        self.messages_heard.append(msg)

    def speak(self):
        """
        used in listen method to respond
        :return:
        """

    def follow_up(self):
        """
        after conversation, used to store data, messages etc from conversation
        :return:
        """
        pass


class ListenerForBalanceRequest(ListenerMessages):

    def __init__(self, messages_heard, netmsginst, msg_type, admin_instance):
        super().__init__(messages_heard=messages_heard, netmsginst=netmsginst, msg_type=msg_type,
                         admin_instance=admin_instance)

    def speak(self):

        if self.messages_heard and self.messages_heard[-1] == self.last_msg:
            self.netmsginst.end_convo = True
            return self.last_msg
        # elif self.messages_heard


class ListenerForSendingTokens(ListenerMessages):

    def __init__(self, messages_heard, netmsginst, msg_type, admin_instance,q_object=None):
        """
        :param messages_heard: this is the two initial messages already heard, list
        :param netmsginst: used to pass the
        :param msg_type: this will be used to determine the validator to call depending on msg type
        """
        super().__init__(messages_heard=messages_heard, netmsginst=netmsginst, msg_type=msg_type,
                         admin_instance=admin_instance)
        self.need_pubkey = b'wpk'
        self.q_object = q_object

    def speak(self):
        """
        [
        used in listen method to respond
        :return:
        """

        try:
            print("in listener")

            if self.messages_heard and self.messages_heard[-1] == self.last_msg:
                self.netmsginst.end_convo = True
                return self.last_msg

            elif self.messages_heard and len(self.messages_heard) == 3:  # This is main msg for validation
                rsp = None
                # self.msg_type will determine the validator to use

                rsp = validator_dict_callable[self.msg_type](
                    json.loads(self.messages_heard[2].decode()),
                    q_object=self.q_object,
                    admin_instance=self.admin_instance,
                ).check_validity()

                print("in ListenerMessages.py, rsp: ", rsp)

                if rsp is None: # wallet_pubkey not in database
                    return self.need_pubkey
                if rsp is True:
                    self.netmsginst.end_convo = True
                    return self.verified_msg
                if rsp is False:
                    self.netmsginst.end_convo = True
                    return self.reject_msg
                else:
                    self.netmsginst.end_convo = True
                    return self.last_msg

            elif len(self.messages_heard) > 3:
                if self.messages_heard[-1] != self.last_msg:  # make sure last msg not b'end' message

                    # if message is not last message then should be wallet pubkey info requested
                    # this will also store wallet info for reuse
                    rsp = validator_dict_callable[self.msg_type](
                        json.loads(self.messages_heard[2].decode()),
                        # wallet_pubkey = son encoded string {"x":base85 str, "y": base85 str}
                        wallet_pubkey=self.messages_heard[-1].decode(),
                        q_object=self.q_object,
                        admin_instance=self.admin_instance,
                    ).check_validity()

                    print("in ListenerMessages.py rsp2: ", rsp)

                    if rsp is True:
                        self.netmsginst.end_convo = True
                        return self.verified_msg
                    elif rsp is False:
                        self.netmsginst.end_convo = True
                        return self.reject_msg

                self.netmsginst.end_convo = True
                return self.last_msg

        except StopIteration:
            self.netmsginst.end_convo = True
            return self.last_msg

    def follow_up(self):
        pass


class ListenerForSendingAddr(ListenerMessages):

    def speak(self):

        if self.messages_heard and self.messages_heard[-1] == self.last_msg:
            self.netmsginst.end_convo = True
            return self.last_msg

        elif self.messages_heard and len(self.messages_heard) == 3: # main msg
            data = retriever_dict_callable[self.msg_type]()


class ListenerForReservingTokens(ListenerForSendingTokens):
    pass


class ListenerForRevokingTokens(ListenerForSendingTokens):
    pass



