from twisted.internet.protocol import Protocol, ReconnectingClientFactory, connectionDone

"""
Used to connect and maintain long lived connections, this is unlike non-admin nodes with short lived connection
When a connection is made, the instance of VeriNodeConnector Protocol sends itself to another process using q_object 
passed to it. The process can then use the Protocol.transport.write and Protocol.transport.loseConnection methods


another instance could be to instantiate a new NetworkPropagator class whenever a reason+hashpreview message is 
received and set

"""


class VeriNodeConnector(Protocol):

    def __init__(self, addr, factory, q_object_from_network_propagator):
        super().__init__()

        self.factory = factory
        self.q_object = q_object_from_network_propagator
        self.addr = addr
        self.sending_convo = 0
        self.receiving_convo = 0

    def dataReceived(self, data):
        """
        when data is received it is sent to Propagator process with self, process then checks
        its connected_protocols_dict to find where self is a key. data == encoded json list. This list can be:
        a: [propagator type, convo id, convo]
        the propagator type can be either 'n', 'h', 's'. n is new convo, 'h' convo from hearer,
        's' convo from speaker, new convo is from speaker class and goes to a hearer class
        :param data:
        :return:
        """

        # when data is received it is sent to Propagator process with self, process then checks
        # its connected_protocols_dict to find where self is a key. data == encoded json list. This list can be:
        # a: [propagator type, convo id, convo]
        # the propagator type can be either 'n', 'h', 's'. n is new convo, 'h' convo from hearer,
        # 's' convo from speaker,
        self.q_object.put([self, data])

    def connectionMade(self):
        """
        when connection is made, send self, NetworkPropagator then can use the transport.write() method to send data
        or transport.loseConnection() to end connection (if during shutdown or if node is malicious)

        A dictionary is created with self as key and a dictionary of dictionaries:
        'speaker' key, has a dictionary with keys of convos in which current node initiated convo (propagating message)
        'hearer' key, has a dictionary with keys of convos which was initiated by other party(receiving valid message)
        :return:
        """
        self.factory.number_of_connections += 1

        self.q_object({self: {"speaker": {}, "hearer": {}}})

    def connectionLost(self, reason=connectionDone):
        self.factory.number_of_connections -= 1


class VeriNodeConnectorFactory(ReconnectingClientFactory):

    def __init__(self, q_object_from_network_propagator, number_of_connections_wanted=2):
        super().__init__()
        self.q_object_from_network_propagator = q_object_from_network_propagator
        self.number_of_wanted_connections = number_of_connections_wanted
        self.number_of_connections = 0
        self.maxRetries = 2

    def buildProtocol(self, addr):

        if self.number_of_connections <= self.number_of_wanted_connections:
            return VeriNodeConnector(addr, self, self.q_object_from_network_propagator)
        else:
            return None
