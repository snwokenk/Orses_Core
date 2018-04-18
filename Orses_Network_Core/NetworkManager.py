from Orses_Network_Core.VeriNodeConnector import VeriNodeConnectorFactory
from Orses_Network_Core.VeriNodeListener import VeriNodeListenerFactory
from Orses_Network_Core.NetworkListener import NetworkListenerFactory
from Orses_Network_Messages_Core.NetworkMessages import NetworkMessages


class NetworkManager:
    def __init__(self, admin, q_object_from_network_propagator):

        self.admin = admin
        self.databases_created = False if admin == None else True # db created when admin created, imported or loaded
        self.addresses = {"127.0.0.1": 55603}
        self.veri_connecting_factory = VeriNodeConnectorFactory(q_object_from_network_propagator)
        self.veri_listening_factory = VeriNodeListenerFactory(q_object_from_network_propagator)

    def run_veri_node_network(self, reactor_instance, q_object_from_network_propagator, q_object_from_competing_process=None):

        veri_listening_factory = VeriNodeListenerFactory(q_object_from_network_propagator)

        for i in self.addresses:
            reactor_instance.connectTCP(
                host=i,
                port=self.addresses[i],
                factory=self.veri_connecting_factory
            )

        reactor_instance.listenTCP(55602, veri_listening_factory)

    def run_regular_node_network(self, reactor_instance, q_object_from_network_propagtor_to_validator):

        # listen for regular traffic on port 55600, if can't listen, try port 55601
        port = 55600
        reactor_instance.listenTCP(55600, )




if __name__ == '__main__':
    pass




