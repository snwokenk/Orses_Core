from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyProtocol, DummyFactory


class DummyNetworkListener(DummyProtocol):
    def __init__(self, factory, message_object):
        super().__init__()
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

    def connectionLost(self, reason="connectionDone"):
        print("connectionLost")
        self.message_object.follow_up()

class DummyNetworkListenerFactory(DummyFactory):
    def __init__(self, spkn_msg_obj_creator, admin, q_obj):
        """

        :param spkn_msg_obj_creator: a callable class, this is used to instatiate a spkn_msg class for each connection
        :param administrator:
        """
        super().__init__()
        self.message_object = spkn_msg_obj_creator
        self.admin = admin
        self.q_object =q_obj

    def buildProtocol(self, addr):

        return DummyNetworkListener(
            factory=self,
            message_object=self.message_object(q_obj=self.q_object, admin_instance=self.admin)
        )

