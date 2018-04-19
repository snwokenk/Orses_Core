from twisted.internet.protocol import Protocol, Factory, connectionDone

"""
Used to listen for long live connections from other veri nodes. ideal connection should be 2 to 4 connections. 
"""


class VeriNodeListener(Protocol):
    def __init__(self, addr, factory, q_object_from_network_propagator):
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
        self.q_object.put([self, data])

    def connectionMade(self):
        """
        when connection is made, send self, NetworkPropagator then can use the transport.write() method to send data
        or transport.loseConnection() to end connection (if during shutdown or if node is malicious)
        :return:
        """
        self.q_object(self)


class VeriNodeListenerFactory(Factory):
    def __init__(self, q_object_from_network_propagator):
        super().__init__()
        self.q_object_from_network_propagator = q_object_from_network_propagator

    def buildProtocol(self, addr):
        return VeriNodeListener(addr, self, self.q_object_from_network_propagator)
