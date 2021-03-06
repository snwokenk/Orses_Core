from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyProtocol, DummyFactory
from Orses_Util_Core.Protocol_ID import ProtoId


class DummyVeriNodeListener(DummyProtocol):

    def __init__(self, addr, factory):
        self.proto_id = ProtoId.protocol_id()  # protocol Id automatically increased for each instance
        super().__init__()
        self.network_sorter = factory.network_sorter
        self.factory = factory
        self.q_object = factory.q_object_from_protocol
        self.addr = addr

    def dataReceived(self, data):
        """
        data received is sent to network_sorter, if it is a msg propagated to current node,
        then it is sent to validator (if validator does not have the required pubkey then a b'wpk" message is sent

         if a new message is being sent by other node, the the first three bytes will be a z, the reason message and -
         This means the first 3 characters must be in {"za-", "zb-", "zc-", "zd-"}
        :param data:
        :return:
        """

        # when data is received it is sent to Propagator process with self, process then checks
        # its connected_protocols_dict to find where self is a key. data == encoded json list. This list can be:
        # a: [propagator type, convo id, convo]
        # the propagator type can be either 'n', 'h', 's'. n is new convo, 'h' convo from hearer,
        # 's' convo from speaker,
        self.q_object.put([self.proto_id, data])

    def connectionMade(self):
        """
        when connection is made, send self, NetworkPropagator then can use the transport.write() method to send data
        or transport.loseConnection() to end connection (if during shutdown or if node is malicious)

        A dictionary is created with self as key and a dictionary of dictionaries:
        'speaker' key, has a dictionary with keys of convos in which current node initiated convo (propagating message)
        'hearer' key, has a dictionary with keys of convos which was initiated by other party(receiving valid message)
        :return:
        """

        # adds protocol to network propagator.connected_protocols_dict
        print("connection made in listener: ", self.addr)
        self.network_sorter.add_protocol(self)

    def connectionLost(self, reason="ConnectionDone"):

        # removes self from connected protocol
        self.network_sorter.remove_protocol(self)


class DummyVeriNodeListenerFactory(DummyFactory):
    def __init__(self, q_object_from_protocol, network_sorter):
        super().__init__()
        self.q_object_from_protocol = q_object_from_protocol
        self.network_sorter = network_sorter

    def buildProtocol(self, addr):
        return DummyVeriNodeListener(addr, self)