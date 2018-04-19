from twisted.internet.protocol import Protocol, ReconnectingClientFactory,connectionDone
"""
Used to connect and maintain long lived connections, this is unlike non-admin nodes with short lived connection
When a connection is made, the instance of VeriNodeConnector Protocol sends itself to another process using q_object 
passed to it. The process can then use the Protocol.transport.write and Protocol.transport.loseConnection methods


another instance could be to instantiate a new NetworkPropagator class whenever a reason+hashpreview message is received and
seting 

"""


class VeriNodeConnector(Protocol):
    def __init__(self, addr,factory, q_object_from_network_propagator):
        super().__init__()

        self.factory = factory
        self.q_object = q_object_from_network_propagator
        self.addr = addr

    def dataReceived(self, data):
        """
        data received is sent to network_propagator, if it is a msg propagated to current node,
        then it is sent to validator (if validator does not have the required pubkey then a b'wpk" message is sent

        :param data:
        :return:
        """

        # when data is received, self is sent with data, receiving process is able to identify the connection sending
        # self is first in list, and data is second.
        self.q_object.put([self, data])

    def connectionMade(self):
        """
        when connection is made, send self, NetworkPropagator then can use the transport.write() method to send data
        or transport.loseConnection() to end connection (if during shutdown or if node is malicious)
        :return:
        """
        self.factory.number_of_connections += 1
        self.q_object(self)

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
