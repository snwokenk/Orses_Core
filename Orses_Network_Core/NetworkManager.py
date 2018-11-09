import traceback

from Orses_Network_Core.VeriNodeConnector import VeriNodeConnectorFactory
from Orses_Network_Core.VeriNodeListener import VeriNodeListenerFactory
from Orses_Network_Core.NetworkListener import NetworkListenerFactory
from Orses_Network_Messages_Core.NetworkMessages import NetworkMessages


# for sandbox mode
from Orses_Dummy_Network_Core.DummyVeriNodeConnector import DummyVeriNodeConnectorFactory
from Orses_Dummy_Network_Core.DummyVeriNodeListener import DummyVeriNodeListenerFactory
from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyReactor


class NetworkManager:
    def __init__(self, admin, q_object_from_protocol, q_object_to_validator, net_msg_sorter, reg_network_sandbox: bool,
                 reactor_inst, reg_listening_port=55600, veri_listening_port=55602, ):

        self.admin = admin
        self.databases_created = False if admin is None else True # db created when admin created, imported or loaded
        self.reg_network_sandbox = reg_network_sandbox
        self.reactor_inst = reactor_inst
        # get sandbox address or live address
        # self.addresses_file = Filenames_VariableNames.default_addr_list_sandbox if self.admin.is_sandbox is True else \
        #     Filenames_VariableNames.default_addr_list

        # self.addresses = FileAction.open_file_from_json(
        #     filename=self.addresses_file,
        #     in_folder=admin.fl.get_username_folder_path()
        # )
        self.addresses = self.admin.get_known_addresses()
        self.listening_port = veri_listening_port
        if admin.is_sandbox is True:

            self.veri_connecting_factory = DummyVeriNodeConnectorFactory(
                q_object_from_protocol=q_object_from_protocol,
                network_sorter=net_msg_sorter
            )

            self.veri_listening_factory = DummyVeriNodeListenerFactory(
                q_object_from_protocol=q_object_from_protocol,
                network_sorter=net_msg_sorter
            )
        else:
            # set listening port

            self.veri_connecting_factory = VeriNodeConnectorFactory(
                q_object_from_protocol=q_object_from_protocol,
                network_sorter=net_msg_sorter
            )
            self.veri_listening_factory = VeriNodeListenerFactory(
                q_object_from_protocol=q_object_from_protocol,
                network_sorter=net_msg_sorter
            )
        self.regular_listening_factory = NetworkListenerFactory(spkn_msg_obj_creator=NetworkMessages, admin=admin,
                                                                q_obj=q_object_to_validator, reactor_inst=reactor_inst)
        self.propagator = net_msg_sorter
        self.regular_listening_port = reg_listening_port


        # use this to store listening ports
        self.Listening_Port_Reg = None
        self.Listening_Port_Veri = None

        # use this to store connected ports
        self.Connected_Port_Veri = list()


    def run_veri_node_network(self, reactor_instance):
        if self.admin.is_sandbox:
            if not isinstance(reactor_instance, DummyReactor):
                return False
        self.Listening_Port_Veri = reactor_instance.listenTCP(self.listening_port, self.veri_listening_factory)
        print(f"in NetworkManager.py addresses {self.addresses}")
        for admin_id in self.addresses:
            addr_list = self.addresses[admin_id]
            self.veri_connecting_factory.change_peer_admin_id(peer_admin_id=admin_id)
            temp_p = reactor_instance.connectTCP(
                host=addr_list[0],
                port=addr_list[1],
                factory=self.veri_connecting_factory
            )
            self.Connected_Port_Veri.append(temp_p)

        return True

    def run_regular_node_network(self, reactor_instance):

        # listen for regular traffic on port 55600, if can't listen, try port 55601
        self.Listening_Port_Reg = reactor_instance.listenTCP(self.regular_listening_port, self.regular_listening_factory)

    def close_all_ports(self):
        # for i in self.Connected_Port_Veri:
        #     i.disconnect()

        try:
            self.Listening_Port_Reg.stopListening()
            self.Listening_Port_Veri.stopListening()
        except Exception as e:
            print("Exception in NetworkManager.py, close_all_ports()")

        print("stopped listening on ports")

    def get_addresses(self):
        return self.admin.known_addresses

    def get_address_of_admin_id(self, admin_id, addresses_dict=None):

        addresses_dict = self.get_addresses() if addresses_dict is None else addresses_dict

        return addresses_dict.get(admin_id, [])

    def connect_to_a_admin(self, admin_id, addresses_dict=None):

        addresses_dict = self.get_addresses() if addresses_dict is None else addresses_dict


        try:
            self.reactor_inst.connectTCP(
                host=addresses_dict[admin_id][0],
                port=addresses_dict[admin_id][1],
                factory=self.veri_connecting_factory
            )
        except KeyError as e:
            print(f"error occurred in NetworkManager connect_to_admin {e}\n"
                  f"printing traceback: ")
            traceback.print_tb(e.__traceback__)

            return False

        return True

    def connect_to_admins(self, list_of_admins, get_addr_for_unknown=False):
        """

        :param list_of_admins: list of admin ids to connect to
        :param get_addr_for_unknown: if this is True, then send a request to other nodes
        :return:
        """

        addresses_dict = self.get_addresses()

        unconnected_admins = list()

        for a_id in list_of_admins:
            if self.connect_to_a_admin(admin_id=a_id, addresses_dict=addresses_dict) is False:
                unconnected_admins.append(a_id)

        if unconnected_admins:
            if get_addr_for_unknown is True:
                # todo: have a way of querying other nodes ( pattern should be request/response
                pass
            else:
                return unconnected_admins
        else:
            return True







if __name__ == '__main__':
    pass




