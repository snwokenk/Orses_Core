

class NetworkResponder:
    """
    used to respond to messages (either send data or receive and execute data
    """

    def __init__(self, admin_inst, mempool, is_sandbox=False, is_root_node=False):
        self.mempool = mempool
        self.is_root_node = is_root_node
        self.is_sandbox = is_sandbox
        self.admin_inst = admin_inst

        # convo_dict[protocol_id] = {convo_id: statementsender/statementreceiver}
        self.convo_dict = dict()
        self.connected_protocols_dict = dict()
        self.connected_protocols_admin_id = dict()

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

    def receive_request(self):
        """
        receive response from
        :return:
        """
        pass

    def execute_request(self):
        """
        based on request execute and send response
        :return:
        """

    def send_response_to_request(self):
        pass