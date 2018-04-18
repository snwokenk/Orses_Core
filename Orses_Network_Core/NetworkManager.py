from Orses_Network_Core.VeriNodeConnector import VeriNodeConnectorFactory
from Orses_Network_Core.VeriNodeListener import VeriNodeListenerFactory
from Orses_Network_Core.NetworkListener import NetworkListenerFactory
from Orses_Network_Messages_Core.NetworkMessages import NetworkMessages


class NetworkManager:
    def __init__(self, admin, q_object_from_network_propagator):

        self.admin = admin
        self.databases_created = False if admin is None else True # db created when admin created, imported or loaded
        self.addresses = {"127.0.0.1": 55603}
        self.veri_connecting_factory = VeriNodeConnectorFactory(q_object_from_network_propagator)
        self.veri_listening_factory = VeriNodeListenerFactory(q_object_from_network_propagator)
        self.regular_listening_factory = NetworkListenerFactory(spkn_msg_obj_creator=NetworkMessages, admin=admin,
                                                                q_obj=q_object_from_network_propagator)

    def run_veri_node_network(self, reactor_instance):

        for i in self.addresses:
            reactor_instance.connectTCP(
                host=i,
                port=self.addresses[i],
                factory=self.veri_connecting_factory
            )

        reactor_instance.listenTCP(55602, self.veri_listening_factory)

    def run_regular_node_network(self, reactor_instance):

        # listen for regular traffic on port 55600, if can't listen, try port 55601
        port = 55600
        reactor_instance.listenTCP(55600, )

    def run_protocol(self, protocol, data, cmd="write"):
        """
        must run with reactor.callFromThread

        :param protocol: a connected instance of Twisted Protocol, should be connected to another verification node
        :param data: encoded(bytes) to write to connected protocol
        :param cmd: "write" or "end_con"
        :return: None
        """

        if cmd == "end_con":
            protocol.loseConnection()
        else:
            protocol.write(data)






if __name__ == '__main__':
    pass




