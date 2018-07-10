"""
Tries to mimic Twisted connection with a dummy internet for a dummy testing network
"""


# todo: when coding, think about the viewpoint of instantiating the DummyInternetClass and then Running the
# todo: veriNode classes in reactor.CallInThread. Methods of the DummyInternetClass will be the only way nodes are
# todo: able to communicate with each other. ie when transport.write() is called have a way to call dataReceived()


class DummyInternetTemplate:
    def __init__(self):
        """
        self.listening_nodes = {
            addr: {
                  port: {
                        factory: factory class for instantiating protocol
                        listener_protocol: connectedInstance
                }

            }

        }
        """
        self.listening_nodes = dict()
        self.address_number = 0
        self.address_to_node_dict = dict()

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
            self._transport = value
        else:
            pass
    @transport.deleter
    def transport(self):
        self._transport = None

    def set_transport_peer_data_received(self, peer_data_received_callable):
        if isinstance(self._transport, DummyTransport):
            self._transport.peer_dataReceived =peer_data_received_callable

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

    def __init__(self):
        self.f_type = "listening"

    def startFactory(self):
        pass

    def buildProtocol(self, addr):
        pass


class DummyClientFactory(DummyFactory):
    """
    meant for connecting
    """

    def __init__(self, ):
        super().__init__()
        self.f_type = "connecting"

    def clientConnectionFailed(self, connector, reason):
        pass

    def clientConnectionLost(self, connector, reason):
        pass

    def startFactory(self):
        """
        will use to connect to listening factory
        :return:
        """
        pass

    def buildProtocol(self, addr):
        return DummyProtocol()


class DummyNode:
    """
    acts as base class dummy node, essentially acts as a container that loads a user
    """

    def __init__(self, admin, dummy_internet, real_reactor_instance):
        self.admin = admin
        self.internet = dummy_internet  # should be an instance of DummyInternet
        self.addr = None
        self.reactor = None
        self.available_ports = set(range(0, 55600)).union(range(55604, 65536))
        self.get_dummy_addr_instantiate_reactor(real_reactor_instance)

    def get_dummy_addr_instantiate_reactor(self, real_reactor_instance):
        """
        override, to get dummy addr from dummy internet
        :return:
        """

        if isinstance(self.internet, DummyInternet):
            self.addr = self.internet.give_address_to_node(instance_of_node=self)
            if isinstance(self.addr, str):
                self.reactor = DummyReactor(node_instance=self, real_reactor_instance=real_reactor_instance)
            else:
                self.addr = None

    def get_a_port(self):
        port_number = self.available_ports.pop()
        return port_number



class DummyClientNode(DummyNode):
    """
    mimic a client Node
    """





class DummyTransport:
    """
    Transport
    """
    def __init__(self, peer_protocol: DummyProtocol, dummy_internet_inst: DummyInternetTemplate,
                 data_access_dict: list, is_listener:bool):
        self.is_listener = is_listener
        self.protocol = peer_protocol
        self.dataReceived = peer_protocol.dataReceived  # calls the dataReceived method off peer protocol
        self.internet = dummy_internet_inst
        self.data_for_listening_dict = data_access_dict # [listener_host, listener_port, listener_protocol, connector_host, connector_port],
        self.host = [data_access_dict[0], data_access_dict[1]] if is_listener else [data_access_dict[3], data_access_dict[4]]
        self.peer = [data_access_dict[0], data_access_dict[1]] if not is_listener else [data_access_dict[3], data_access_dict[4]]

    def write(self, data: bytes):
        if callable(self.dataReceived):
            self.dataReceived(data=data)

    def loseConnection(self):

        self.internet.disconnect(self.data_for_listening_dict)
        del self.protocol.transport
        self.protocol = None
        self.dataReceived = None
        self.internet = None
        self.data_for_listening_dict = None

    def getPeer(self):
        return self.peer

    def getHost(self):
        return self.host


class DummyReactor:
    def __init__(self, node_instance: DummyNode, real_reactor_instance):
        self.node = node_instance
        self.real_reactor_instance = real_reactor_instance
        self.node_host_addr = self.node.addr #addr
        self.node_dummy_internet = self.node.internet
        self.port_to_factory_dict = dict()  # {port: [listening_factory, backlog or max connections]}
        self.running = False

    """
    Methods mimicking twisteds reactor
    """
    def listenTCP(self, port, factory, backlog=50):

        success = self.node_dummy_internet.add_to_listening(
            addr=self.node_host_addr,
            port=port,
            factory=factory,
            listening_node=self.node
        )
        if success is True:
            self.port_to_factory_dict[port] = [factory, backlog]
        elif success is None:
            print(f"Log Message at listenTCP: {self.node} with address {self.node_host_addr} "
                  f"is already listening on port {port} ")  # this should be logged

    def connectTCP(self, host, port, factory: DummyClientFactory):


        # todo: use connector to have a way for retrying connection

        connected_instance = self.node_dummy_internet.connect_to_listening(
            connecting_addr=[self.node_host_addr, self.node.get_a_port()],
            listening_addr=[host, port],
            connector_factory=factory,
            connector_node=self.node
        )

        if connected_instance is False:
            factory.clientConnectionFailed(connector=None, reason="No Listening Node In Addr")

        return port

    def callLater(self, delay, callable_func, *args, **kw):
        if self.real_reactor_instance.running:  # this might change, probably have to pass reactor instance
            self.real_reactor_instance.callLater(delay, callable_func, *args, **kw)

    def callFromThread(self, callable_func, *args, **kw):
        self.real_reactor_instance.callFromThread(callable_func, *args, **kw)

    def callInThread(self, callable_func, *args, **kw):
        self.real_reactor_instance.callInThread(callable_func, *args, **kw)

    def run(self):
        self.running = True

    def stop(self):
        self.running = False

    """
    these methods not mimicking any functions in twisted
    """


class ConnectedInstance:
    """
    will represent a connected instance
    """

    def __init__(self, connector_protocol, listener_protocol, connector_port_addr, listener_port_addr):
        self._connector_protocol = connector_protocol
        self._connector_port = connector_port_addr[1]
        self._connector_host = connector_port_addr[0]  # address
        self._listener_protocol = listener_protocol
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


class DummyInternet(DummyInternetTemplate):

    def __init__(self):
        """
        self.listening_nodes = {
            addr: {
                  port: {
                        factory: factory class for instantiating protocol
                        listener_protocol: connectedInstance
                }

            }

        }
        """
        super().__init__()

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

    def add_to_listening(self, addr, port, factory, listening_node: DummyNode):
        """

        :param addr: address of node trying to listen
        :param port: port on which to listen
        :param factory: factory instance for listening
        :return: bool
        """

        if addr in self.address_to_node_dict and self.address_to_node_dict[addr] == listening_node and port <= 65535:
            if isinstance(factory, DummyInternet):
                if addr in self.listening_nodes:
                    if port in self.listening_nodes[addr]:
                        return None
                    else:
                        self.listening_nodes[addr][port] = {
                            "factory": factory
                        }
                else:
                    self.listening_nodes[addr] = {
                        port: {
                            "factory": factory
                        }
                    }

                return True

        return False




    def connect_to_listening(self, connecting_addr, listening_addr, connector_factory: DummyClientFactory,
                             connector_node: DummyNode):

        listener_host = listening_addr[0]
        listener_port = listening_addr[1]
        connector_host = connecting_addr[0]
        connector_port = connecting_addr[1]

        if listener_host in self.listening_nodes and listener_port in self.listening_nodes[listener_host]:
            try:
                tmp_node = self.address_to_node_dict[connector_host]
            except KeyError:
                print("Please call give_address_to_node() to get an address")
                return None  # connecting node not connected to DummyInternet and not in address dictionary
            else:
                if tmp_node == connector_node:  # checks to make sure node at address same node sending

                    # get listener factory instance
                    listener_factory = self.listening_nodes[listener_host][listener_port]["factory"]

                    # create protocol for listenier
                    listener_protocol = listener_factory.buildProtocol(addr=[connector_host, connector_port])

                    # create protocol for connector
                    connector_protocol = connector_factory.buildProtocol(addr=[listener_host, listener_port])

                    transport_for_listener = DummyTransport(
                        peer_protocol=connector_protocol,
                        dummy_internet_inst=self,
                        data_access_dict=[listener_host, listener_port, listener_protocol, connector_host, connector_port],
                        is_listener=True
                    )
                    listener_protocol.transport = transport_for_listener
                    transport_for_connector = DummyTransport(
                        peer_protocol=listener_protocol,
                        dummy_internet_inst=self,
                        data_access_dict=[listener_host, listener_port, listener_protocol, connector_host, connector_port],
                        is_listener=False
                    )
                    connector_protocol.transport = transport_for_connector
                    connected_inst = ConnectedInstance(
                        connector_protocol=connector_protocol,
                        listener_protocol=listener_protocol,
                        connector_port_addr=[connector_host, connector_port],
                        listener_port_addr=[listener_host, listener_port]
                    )

                    self.listening_nodes[listener_host][listener_port][listener_protocol] = connected_inst
                   # call connectionMade methods of listener protocol and connector_protocol
                    listener_protocol.connectionMade()
                    connector_protocol.connectionMade()

                    return True
        else:
            return False

    def disconnect(self, data_access_dict: list):
        try:
            del self.listening_nodes[data_access_dict[0]][data_access_dict[1]][data_access_dict[2]]

        except KeyError:
            return False

        else:
            return True



    def run_dummy_internet(self):
        pass



if __name__ == '__main__':
    pass
