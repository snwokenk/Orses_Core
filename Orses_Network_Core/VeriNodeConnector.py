from twisted.internet.protocol import Protocol, ReconnectingClientFactory,connectionDone
"""
Used to connect and maintain long lived connections, this is unlike non-admin nodes with short lived connection
the protocol then receives/sends message through a queue object from/to NetworkPropagator class


"""


class VeriNodeConnector(Protocol):
    def __init__(self, q_object_from_network_propagator):
        super().__init__()

        self.q_object = q_object_from_network_propagator

    def dataReceived(self, data):
        """
        data received is sent to network_propagator, if it is a msg propagated to current node,
        then it is sent to validator (if validator does not have the required pubkey then a b'wpk" message is sent

        :param data:
        :return:
        """
        self.q_object.put(data)

    def connectionMade(self):
        """
        when connection is made, send self, NetworkPropagator then can use the transport.write() method to send data
        or transport.loseConnection() to end connection (if during shutdown or if node is malicious)
        :return:
        """
        self.q_object(self)



class VeriNodeConnectorFactory(ReconnectingClientFactory):
    pass