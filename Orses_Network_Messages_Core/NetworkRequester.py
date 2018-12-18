import json, multiprocessing


class NetworkRequester:
    """
    Used to send request message (either to get data or modify/send data

    request message is a list: ie req_list
    [msg_id, type of request (GET or POST), if msg is blockchain related or regular network related,
        type of msg, msg]

    """

    def __init__(self, admin_inst, mempool, reactor_inst, is_sandbox=False, is_root_node=False):
        self.reactor_inst = reactor_inst
        self.mempool = mempool
        self.is_root_node = is_root_node
        self.is_sandbox = is_sandbox
        self.admin_inst = admin_inst

        # convo_dict[protocol_id] = {convo_id: statementsender/statementreceiver}
        self.convo_dict = dict()
        self.connected_protocols_dict = dict()
        self.connected_protocols_admin_id = dict()

    class ReceiveResponse:

        def __init__(self, q_obj, convo_id):
            self.convo_id = convo_id
            self.q_obj = q_obj
            self.end_convo = False
            self.response = None

        def send_response(self, response):
            """
            used by networksorter or networkpropagator to send response to class when received by
            other node
            :param response:
            :return:
            """
            self.response = response
            self.q_obj.put(response)

        def get_response(self):
            self.end_convo = True
            if self.response:
                return self.response
            return self.q_obj.get()

    def ___get_convo_id(self, protocol_id, ):

        return get_convo_id(
            protocol_id=protocol_id,
            req_inst=self
        )

    def add_protocol(self, protocol, peer_admin_id=None):

        # adds connected protocol, key as protocol_id,  value: list [protocol object,
        # number of convo(goes to 20000 and resets)]
        self.connected_protocols_dict.update({protocol.proto_id: [protocol, 0]})
        self.convo_dict[protocol.proto_id] = dict()
        self.connected_protocols_admin_id[peer_admin_id] = protocol

    def remove_protocol(self, protocol):
        del self.connected_protocols_admin_id[protocol.peer_admin_id]
        del self.connected_protocols_dict[protocol.proto_id]
        del self.convo_dict[protocol.proto_id]

    def send_request(self, type_of_req: str, is_blockchain: bool, type_of_msg: str, msg, peer_admin):

        protocol = self.connected_protocols_admin_id.get(peer_admin, None)

        if not protocol:
            return False
        convo_id = self.___get_convo_id(protocol_id=protocol.proto_id)
        req_msg = [convo_id,
                   type_of_req,
                   is_blockchain,
                   type_of_msg,
                   msg
                   ]

        receive_response_inst = self.ReceiveResponse(
            q_obj=multiprocessing.Queue(),
            convo_id=convo_id
        )

        self.speaker(
            msg=req_msg,
            protocol=protocol
        )

    def speaker(self, msg, protocol):

        json_msg = json.dumps(msg)
        self.reactor_inst.callFromThread(
            protocol.transport.write,
            json_msg.encode()
        )



def get_convo_id(protocol_id, req_inst: NetworkRequester):

    while True:  # gets a convo id that is not in use
        convo_id = req_inst.connected_protocols_dict[protocol_id][1]
        if convo_id in req_inst.convo_dict[protocol_id] and req_inst.convo_dict[protocol_id][convo_id].end_convo is False:
            req_inst.connected_protocols_dict[protocol_id][1] += 1
            continue
        elif convo_id >= 20000:
            req_inst.connected_protocols_dict[protocol_id][1] = 0
            continue
        req_inst.connected_protocols_dict[protocol_id][1] += 1
        return convo_id