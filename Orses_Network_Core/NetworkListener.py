from twisted.internet.protocol import Protocol, Factory, connectionDone

"""
The goal of the NetworkListener protocol and factory is to be used to listen for network messages from other 
non veri nodes. For connections from veri nodes the VeriNodeListener and VeriNodeConnector classes will be used
This class implementation is exclusively used by veri nodes or nodes (later on) offering internet facing services 
on the orses network

1. The classes in this file will be instantiated by methods in the NetworkManager class 
    in folder "Orses_Network_Core"
2. The classes in this file will be instantiated with a message object(depending on the type of message)
3. This message object for a server protocol/factory will be a "Listener" message object and will manage network 
    conversations with a "Speaker" message object of a Client protocol/factory

"""


class NetworkListener(Protocol):
    def __init__(self, factory, message_object):
        Protocol().__init__()
        self.factory = factory
        self.message_object = message_object

    def dataReceived(self, data):
        print("rec: ", data)
        self.message_object.listen(data)

        rsp = self.message_object.speak()
        print("resp: ", rsp)

        self.transport.write(rsp)

        if self.message_object.end_convo is True:
            self.transport.loseConnection()

    def connectionMade(self):
        pass

    def connectionLost(self, reason=connectionDone):
        print("connectionLost")
        self.message_object.follow_up()


class NetworkListenerFactory(Factory):

    def __init__(self, spkn_msg_obj_creator, admin, q_obj):
        """

        :param spkn_msg_obj_creator: a callable class, this is used to instatiate a spkn_msg class for each connection
        :param administrator:
        """
        Factory().__init__()
        self.message_object = spkn_msg_obj_creator
        self.admin = admin
        self.q_object =q_obj

    def buildProtocol(self, addr):
        return NetworkListener(factory=self, message_object=self.message_object(q_obj=self.q_object))