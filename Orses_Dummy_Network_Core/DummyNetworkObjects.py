"""
Tries to mimic Twisted connection with a dummy internet for a dummy testing network
"""

class DummyProtocol:
    """
    have standard protocol attributes and methods
    """
    def __init__(self):
        self.transport = None

    def makeConnection(self, transport):
        """
        do not overwrite
        :param transport:
        :return:
        """
        self.transport = transport
        self.connectionMade()

    def connectionMade(self):
        pass

    def connectionLost(self, reason):
        """

        :param reason: should state reason for connection ending
        :return:
        """

        pass

    def dataReceived(self, data: bytes):
        """
        used to send data
        :param data:
        :return:
        """


class DummyFactory:
    """
    meant for listening
    """

    def __init__(self, self_addr):
        self.f_type = "listening"
        self.self_addr = self_addr

    def startFactory(self):
        pass

    def buildProtocol(self, addr):
        pass


class DummyClientFactory(DummyFactory):
    """
    meant for connecting
    """

    def __init__(self, self_addr):
        super().__init__(self_addr)
        self.f_type = "connecting"

    def startFactory(self):
        """
        will use to connect to listening factory
        :return:
        """
        pass

    def buildProtocol(self, addr):
        pass


class DummyTransport:
    def __init__(self, peer, host, q_object):
        self.peer = peer
        self.host = host
        self.q_object = q_object

    def write(self, data: bytes):
        self.q_object.put(data)

    def loseConnection(self):
        pass

    def getPeer(self):
        pass

    def getHost(self):
        pass


class DummyNode:
    """
    acts as dummy node, essentially acts as a container that loads a user
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password


class DummyAdminNode(DummyNode):

    def __init__(self, username, password, new_admin, isCompetitor):

        super().__init__(username=username, password=password)

        self.new_admin = new_admin
        self.is_competitor = isCompetitor



class DummyInternet:

    def __init__(self):
        """
        self.listening admins = {
        key = addr
        value = instance of DummyFactory or childresn
        }
        """
        self.listening_admins = dict()
        self.addresses = 0

    def give_address_to_admin__process(self):
        pass

    def add_to_listening(self, admin_interface, admin_factory):
        pass

    def connect_to_listening(self, addr):
        pass

    def run_dummy_internet(self):
        pass



if __name__ == '__main__':
    pass
