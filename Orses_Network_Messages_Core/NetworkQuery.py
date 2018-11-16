import json, multiprocessing
from queue import Empty
from Orses_Network_Messages_Core.QueryClass import dict_of_query_callable

# todo: Use a Queue object to pass info


class NetworkQuery:

    # {query_id: sender class
    dict_of_active_queries = dict()





    @classmethod
    def send_sequential_query(cls, query_msg, admin_inst, list_of_protocols, a_callable=None):
        """
        used to send find an information online (a block, an adddress or addresses, etc)
        :param query_msg:
        :param admin_inst:
        :param list_of_protocols: list of protocols to send to
        :param a_callable: callback function to be called when done
        :return:
        """
        for protocol in list_of_protocols:


            rsp = cls.send_a_query(
                query_msg=query_msg,
                admin_inst=admin_inst,
                protocol=protocol
            )

            if rsp:
                if callable(a_callable):
                    a_callable(rsp)
                return rsp

        return []



    @classmethod
    def send_a_query(cls, query_msg, admin_inst, protocol, a_callable=None, **kwargs):
        """
        Used to send a query (request/response). If a_callable is None or not callable it will block
        if a_callable is callable then it will not block and response will be sent using a_callable as
        a callback function

        Blocking is is timed out at 15 seconds
        :param query_msg:
        :param admin_inst:
        :param protocol:
        :param a_callable:
        :param kwargs:
        :return:
        """

        q = multiprocessing.Queue()

        qs = QuerySender(
            admin_inst=admin_inst,
            protocol=protocol,
            a_callable=a_callable if callable(a_callable) else lambda x:  q.put(x)

        )
        cls.dict_of_active_queries[qs.convo_id] = qs
        qs.send(query_msg=query_msg)

        # *** when response is sent, NetworkMessageSorter will call the receive() associated with convo
        # *** id. This in turn calls the callback function
        if callable(a_callable) is False:
            try:
                # will block for 15 seconds
                rsp = q.get(timeout=15)
            except Empty:
                print(f"Other node did not respond on time, in NetworkQuery")
                rsp = None
            return rsp


    @staticmethod
    def respond_to_a_query(query_msg, admin_inst, protocol, **kwargs):

        qr = QueryResponder(
            admin_inst=admin_inst,
            protocol=protocol,

        )
        qr.listen(query_msg=query_msg)

    @classmethod
    def receive_query_response(cls, query_msg):
        convo_id = query_msg[1]
        response = query_msg[2]

        qs = cls.dict_of_active_queries[convo_id]

        # this will call the callback function passed when sending. Usually this function has a queue obj
        qs.receive(response)


class QuerySender:

    convo_id = 0

    def __init__(self, admin_inst, protocol, a_callable):
        self.propagator_inst = admin_inst.get_net_propagator()
        self.admin_inst = admin_inst
        self.protocol = protocol
        self.prop_type = 'q'
        self.type_of_msg = 'req'
        self.convo_id = str(QuerySender.convo_id)
        QuerySender.convo_id += 1
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
            QuerySender.convo_id -= 1
            self.response_msg = response
            self.a_callable(response)

    def speaker(self, msg):
        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, self.type_of_msg, msg]).encode()
        )


class QueryResponder:

    def __init__(self, admin_inst, protocol):
        self.propagator_inst = admin_inst.get_net_propagator()
        self.admin_inst = admin_inst
        self.protocol = protocol
        self.prop_type = 'q'
        self.type_of_msg = 'rsp'
        self.sent_rsp = False
        self.response_msg = None

    def listen(self, query_msg):
        """

        :param query_msg: list with [prop_type == 'q', convo_id, [query id, arguments for callable] ]
        :return:
        """
        def listen_in_another_thread():
            convo_id = query_msg[1]
            main_msg = query_msg[2]
            query_id = main_msg[0]
            a_callable = dict_of_query_callable.get(query_id)

            if isinstance(query_msg[1], list):
                response = a_callable(admin_inst=self.admin_inst, *query_msg[1])

            else:
                response = []

            self.speak(response=response, convo_id=convo_id)

        self.propagator_inst.reactor_instance.callFromThread(

        )

    def speak(self, response, convo_id):

        if self.sent_rsp is False:
            self.sent_rsp = True

            self.speaker(msg=response, convo_id=convo_id)

    def speaker(self, msg, convo_id):
        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, convo_id, self.type_of_msg, msg]).encode()
        )
