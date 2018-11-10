import json

from Orses_Network_Messages_Core.QueryClass import dict_of_query_callable


class QuerySender:

    def __init__(self, admin_inst, protocol, convo_id, a_callable):
        self.propagator_inst = admin_inst.get_net_propagator()
        self.admin_inst = admin_inst
        self.protocol = protocol
        self.prop_type = 'q'
        self.convo_id = convo_id
        self.sent_msg = False
        self.rcv_rsp = False
        self.response_msg = None
        self.a_callable = a_callable

    def send(self, query_msg):

        if self.sent_msg is False:
            self.sent_msg = True
            self.speaker(msg=query_msg)

    def receive(self, response):
        if self.rcv_rsp is False:
            self.rcv_rsp = True
            self.response_msg = response
            self.a_callable(response)

    def speaker(self, msg):
        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )


class QueryResponder:

    def __init__(self, admin_inst, protocol, convo_id, a_callable):
        self.propagator_inst = admin_inst.get_net_propagator()
        self.admin_inst = admin_inst
        self.protocol = protocol
        self.prop_type = 'q'
        self.convo_id = convo_id
        self.sent_rsp = False
        self.response_msg = None
        self.a_callable = a_callable

    def listen(self, query_msg):
        """

        :param query_msg: list with [query id, arguments for callable
        :return:
        """

        a_callable = dict_of_query_callable.get(query_msg[0])

        if isinstance(query_msg[1], list):
            response = a_callable(admin_inst=self.admin_inst, *query_msg[1])

        else:
            response = []

        self.speak(response=response)

    def speak(self, response):

        if self.sent_rsp is False:
            self.sent_rsp = True

            self.speaker(msg=response)

    def speaker(self, msg):
        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )
