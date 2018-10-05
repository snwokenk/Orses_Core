from Orses_Network_Messages_Core import ListenerMessages

dict_of_listening_types = dict()
dict_of_listening_types["tx_asg"] = ListenerMessages.ListenerForSendingTokens
dict_of_listening_types["tx_ttx"] = ListenerMessages.ListenerForSendingTokens
dict_of_listening_types["tx_trr"] = ListenerMessages.ListenerForReservingTokens
dict_of_listening_types["tx_trx"] = ListenerMessages.ListenerForRevokingTokens
dict_of_listening_types["rq_adr"] = ListenerMessages.ListenerForSendingAddr
dict_of_listening_types["rq_bal"] = ListenerMessages.ListenerForBalanceRequest


class NetworkMessages:
    """
    class is to listen for first 2 messages, then choose which ListenerMessages class to use
    """

    def __init__(self, admin_instance, q_obj=None):

        self.admin_instance=admin_instance
        self.first_two_msgs = list()
        self.message_object = None
        self.valid_first_msg = {b'rcn', b'rcnv'}
        self.valid_second_msg = {b'tx_asg', b'tx_ttx', b'tx_trr', b'tx_trx', b'rq_adr', b'rq_bal', b'misc_msg'}
        self.last_msg = b'end'
        self.ack_msg = b'ack'
        self.reject_msg = b'rej'
        self.q_obj = q_obj
        self.end_convo = False

    def listen(self, msg):

        if len(self.first_two_msgs) < 2:
            self.first_two_msgs.append(msg)
        elif self.message_object:
            self.message_object.listen(msg)
        elif self.message_object is None:
            # instantiates the message object based on the second msg
            # uses the instantiated listen() method to start listening
            type_key = self.first_two_msgs[-1].decode()
            try:
                self.message_object = dict_of_listening_types[type_key](
                    messages_heard=self.first_two_msgs,
                    netmsginst=self,
                    msg_type=type_key,
                    q_object=self.q_obj,
                    admin_instance=self.admin_instance
                )
                self.message_object.listen(msg)
            except KeyError:
                return self.last_msg

    def speak(self):

        if len(self.first_two_msgs) == 1 and self.first_two_msgs[-1] in self.valid_first_msg:
            return self.ack_msg
        elif len(self.first_two_msgs) == 2 and self.first_two_msgs[-1] in self.valid_second_msg and \
            not self.message_object:
            return self.ack_msg
        elif len(self.first_two_msgs) > 2 and self.first_two_msgs[1] in self.valid_second_msg\
            and self.message_object:
            return self.message_object.speak()
        else:
            # print("len ", len(self.first_two_msgs), "\nlast message: ",self.first_two_msgs[-1], "\nmessage object: ", self.message_object)
            self.end_convo = True
            return self.last_msg

    def follow_up(self):
        """
        calls the instantiated message object's follow up method.
        if message object is None, then pass
        :return:
        """

        if self.message_object:
            self.message_object.follow_up()


