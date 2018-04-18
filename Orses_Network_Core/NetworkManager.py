from Orses_Network_Core.VeriNodeConnector import VeriNodeConnectorFactory
from Orses_Network_Core.VeriNodeListener import VeriNodeListenerFactory


class NetworkManager:
    def __init__(self, admin):

        self.admin = admin


def run_veri_node_network(reactor_instance, q_object_from_network_propagator, q_object_from_competing_process=None):
    addresses = {"127.0.0.1": 55602}

    veri_connecting_factory = VeriNodeConnectorFactory(q_object_from_network_propagator)
    veri_listening_factory = VeriNodeListenerFactory(q_object_from_network_propagator)

    for i in addresses:
        reactor_instance.connectTCP(
            host=i,
            port=addresses[i],
            factory=veri_connecting_factory
        )




if __name__ == '__main__':
    pass




