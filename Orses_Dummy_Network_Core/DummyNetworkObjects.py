"""
Tries to mimic Twisted connection with a dummy internet for a dummy testing network
"""
from twisted.internet import reactor, defer, threads

class DummyProtocol:
    """
    have standard protocol attributes and methods
    """
    def __init__(self):
        self._transport = None

    @property
    def transport(self):
        return self._transport

    @transport.setter
    def transport(self, value):
        if isinstance(value, DummyTransport):
            self.transport = value
        else:
            pass

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
        return DummyProtocol()


class DummyTransport:
    def __init__(self):
        self.peer = None
        self.host = None

    def write(self, data: bytes):
        pass

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

    def __init__(self, username, password, dummy_internet: DummyInternet):
        self.username = username
        self.password = password
        self.internet = dummy_internet  # should be an instance of DummyInternet
        self.addr = None
        self.reactor = None
        self.available_ports = set(range(0, 55600)).union(range(55604, 65536))
        self.get_dummy_addr_instantiate_reactor()

    def get_dummy_addr_instantiate_reactor(self):
        """
        override, to get dummy addr from dummy internet
        :return:
        """

        if isinstance(self.internet, DummyInternet):
            self.addr = self.internet.give_address_to_node(instance_of_node=self)
            if isinstance(self.addr, str):
                self.reactor = DummyReactor(node_instance=self)
            else:
                self.addr = None

    def get_a_port(self):
        port_number = self.available_ports.pop()
        return port_number



class DummyClientNode(DummyNode):
    """
    mimic a client Node
    """


class DummyAdminNode(DummyNode):
    """
    mimic an admin node
    """

    def __init__(self, username, password, new_admin, isCompetitor, dummy_internet=None):

        super().__init__(username=username, password=password, dummy_internet=dummy_internet)

        self.new_admin = new_admin
        self.is_competitor = isCompetitor


class DummyReactor:
    def __init__(self, node_instance: DummyNode):
        self.node = node_instance
        self.node_host_addr = self.node.addr
        self.node_dummy_internet = self.node.internet
        self.port_to_factory_dict = dict()  # {port: [listening_factory, backlog or max connections]}

    """
    Methods mimicking twisteds reactor
    """
    def listenTCP(self, port, factory, backlog=50):
        success = self.node_dummy_internet.add_to_listening(addr=self.node_host_addr, port=port)
        if success:
            self.port_to_factory_dict[port] = [factory, backlog]

    def connectTCP(self, host, port, factory: DummyClientFactory):

        transport = DummyTransport()

        protocol = factory.buildProtocol(addr=[port, host])
        protocol.transport = transport

        temp_conn_inst = ConnectedInstance(
            connector_protocol=protocol,
            connector_port_addr=[self.node_host_addr, self.node.get_a_port()],
            listener_port_addr=[host, port]
        )

        fully_conn_inst = self.node_dummy_internet.connect_to_listening(
            temp_connected_instance=temp_conn_inst,
            node=self.node
        )

        pass

    def callLater(self, delay, callable_func, *args, **kw):
        if reactor.running:  # this might change, probably have to pass reactor instance
            reactor.callLater(delay, callable_func, *args, **kw)

    def callFromThread(self, callable_func, *args, **kw):
        reactor.callFromThread(callable_func, *args, **kw)

    def callInThread(self, callable_func, *args, **kw):
        reactor.callInThread(callable_func, *args, **kw)

    """
    these methods not mimicking any functions in twisted
    """

    def receive_connection(self, connect_instance: ConnectedInstance):
        """
        should look at port and then use factory to return a protcol using buildProtocol
        :param port:
        :return:
        """
        port = connect_instance

        if port in self.port_to_factory_dict and not isinstance(self.port_to_factory_dict[port][0], DummyClientFactory):

            return True
        else:
            return False


class ConnectedInstance:
    """
    will represent a connected instance
    """

    def __init__(self, connector_protocol, connector_port_addr, listener_port_addr):
        self._connector_protocol = connector_protocol
        self._connector_port = connector_port_addr[1]
        self._connector_host = connector_port_addr[0]  # address
        self._listener_protocol = None
        self._listener_port = listener_port_addr[1]
        self._listener_host = listener_port_addr[0]

    @property
    def connector_protocol(self):
        return self._connector_protocol

    @connector_protocol.setter
    def connector_protocol(self, value):
        if isinstance(value, DummyClientFactory):
            self._connector_protocol = value
        else:
            print("in ConnectedInstance init, connector protocol not right class")
            self._connector_protocol = None

    @property
    def connector_port(self):
        return self._connector_port

    @connector_port.setter
    def connector_port(self, value):
        if isinstance(value, int):
            self._connector_port = value
        else:
            self._connector_port = -1

    @property
    def connector_host(self):
        return self._connector_host

    @connector_host.setter
    def connector_host(self, value):

        if isinstance(value, str):
            self._connector_host = value
        else:
            self._connector_host = ""

    @property
    def listener_protocol(self):
        return self._listener_protocol

    @listener_protocol.setter
    def listener_protocol(self, value):
        if not isinstance(value, DummyClientFactory) and isinstance(value, DummyFactory):
            self._listener_protocol = value
        else:
            print("in ConnectedInstance init, connector protocol not right class")
            self._listener_protocol = None

    @property
    def listener_port(self):
        return self._listener_port

    @listener_port.setter
    def listener_port(self, value):
        if isinstance(value, int):
            self._listener_port = value
        else:
            self._listener_port = -1

    @property
    def listener_host(self):
        return self._listener_host

    @listener_host.setter
    def listener_host(self, value):
        if isinstance(value, str):
            self._listener_host = value
        else:
            self._listener_host = ""


class DummyInternet:

    def __init__(self):
        """
        self.listening_nodes = {
            addr: {
                  port: {
                        listener protocol: connecting_protocol
                }

            }

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



    def add_to_listening(self, addr, port):
        pass

    def connect_to_listening(self, temp_connected_instance: ConnectedInstance, node: DummyNode):
        pass


    def run_dummy_internet(self):
        pass



if __name__ == '__main__':
    pass
