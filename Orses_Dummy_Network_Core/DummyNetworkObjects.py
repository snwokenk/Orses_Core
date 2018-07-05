"""
Tries to mimic Twisted connection with a dummy internet for a dummy testing network
"""


class DummyProtocol:
    """
    have standard protocol attributes and methods
    """
    def __init__(self, transport):
        self.transport = transport

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
    acts as base class dummy node, essentially acts as a container that loads a user
    """

    def __init__(self, username, password, dummy_internet=None):
        self.username = username
        self.password = password
        self.internet = dummy_internet  # should be an instance of DummyInternet
        self.addr = None
        self.reactor = None

    def get_dummy_addr_instantiate_reactor(self):
        """
        override, to get dummy addr from dummy internet
        :return:
        """

        if isinstance(self.internet, DummyInternet):
            self.addr = self.internet.give_address_to_node(instance_of_node=self)
            if isinstance(self.addr, str):
                self.reactor = DummyReactor(node_instance=self)


class DummyClientNode(DummyNode):
    """
    mimic a client Node
    """

class DummyAdminNode(DummyNode):
    """
    mimic an admin node
    """

    def __init__(self, username, password, new_admin, isCompetitor):

        super().__init__(username=username, password=password)

        self.new_admin = new_admin
        self.is_competitor = isCompetitor


class DummyReactor:
    def __init__(self, node_instance):
        self.node = node_instance
        self.node_host_addr = self.node.addr


    @staticmethod
    def listenTCP():
        pass

    @staticmethod
    def connectTCP():
        pass


class DummyInternet:

    def __init__(self):
        """
        self.listening admins = {
        key = addr
        value = instance of DummyFactory or childresn
        }
        """
        self.listening_nodes = dict()
        self.address_number = 0
        self.address_to_node_dict = dict()
        self.q_obj = None

    def give_address_to_node(self, instance_of_node):
        """
        gets an instance of node and adds to address_node_to_dict by assigning address
        address 0 is given to the very first dummy node, this is also the default address for other dummy nodes

        :return:
        """

        if isinstance(instance_of_node, DummyNode):
            temp_addr = str(self.address_number)
            self.address_number += 1
            self.address_to_node_dict[temp_addr] = instance_of_node

            return temp_addr
        else:
            return ""  # if instance_of_node is not an instance of DummyNode or Derived Classes





    def add_to_listening(self, admin_interface, admin_factory):
        pass

    def connect_to_listening(self, addr):
        pass

    def run_dummy_internet(self):
        pass



if __name__ == '__main__':
    pass
