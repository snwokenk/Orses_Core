from Orses_Network_Core.VeriNodeConnector import VeriNodeConnectorFactory
from Orses_Network_Core.VeriNodeListener import VeriNodeListenerFactory
from Orses_Network_Core.NetworkListener import NetworkListenerFactory
from Orses_Network_Messages_Core.NetworkMessages import NetworkMessages
from Orses_Util_Core.FileAction import FileAction
from Orses_Util_Core import Filenames_VariableNames

# for sandbox mode
from Orses_Dummy_Network_Core.DummyVeriNodeConnector import DummyVeriNodeConnectorFactory
from Orses_Dummy_Network_Core.DummyVeriNodeListener import DummyVeriNodeListenerFactory
from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyReactor


class NetworkManager:
    def __init__(self, admin, q_object_from_protocol, q_object_to_validator, propagator, reg_network_sandbox: bool,
                 reg_listening_port=55600, veri_listening_port=55602):

        self.admin = admin
        self.databases_created = False if admin is None else True # db created when admin created, imported or loaded
        self.reg_network_sandbox = reg_network_sandbox
        # get sandbox address or live address
        self.addresses_file = Filenames_VariableNames.default_addr_list_sandbox if self.admin.is_sandbox is True else \
            Filenames_VariableNames.default_addr_list

        self.addresses = FileAction.open_file_from_json(
            filename=self.addresses_file,
            in_folder=admin.fl.get_username_folder_path()
        )
        print(f"in networkmanager.py: addresses: {self.addresses_file}, folder {admin.fl.get_username_folder_path()}")
        self.listening_port = veri_listening_port
        if admin.is_sandbox is True:

            self.veri_connecting_factory = DummyVeriNodeConnectorFactory(
                q_object_from_protocol=q_object_from_protocol,
                propagator=propagator
            )

            self.veri_listening_factory = DummyVeriNodeListenerFactory(
                q_object_from_protocol=q_object_from_protocol,
                propagator=propagator
            )
        else:
            # set listening port

            self.veri_connecting_factory = VeriNodeConnectorFactory(
                q_object_from_protocol=q_object_from_protocol,
                propagator=propagator
            )
            self.veri_listening_factory = VeriNodeListenerFactory(
                q_object_from_protocol=q_object_from_protocol,
                propagator=propagator
            )
        self.regular_listening_factory = NetworkListenerFactory(spkn_msg_obj_creator=NetworkMessages, admin=admin,
                                                                q_obj=q_object_to_validator)
        self.propagator = propagator
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

        print("in Network manager: addresses: ", self.addresses, self.addresses_file)
        for i in self.addresses:
            temp_p = reactor_instance.connectTCP(
                host=i,
                port=self.addresses[i],
                factory=self.veri_connecting_factory
            )
            print("connected Port", temp_p)
            self.Connected_Port_Veri.append(temp_p)

        self.Listening_Port_Veri = reactor_instance.listenTCP(self.listening_port, self.veri_listening_factory)

        return True

    def run_regular_node_network(self, reactor_instance):

        # listen for regular traffic on port 55600, if can't listen, try port 55601
        self.Listening_Port_Reg = reactor_instance.listenTCP(self.regular_listening_port, self.regular_listening_factory)

    def close_all_ports(self):
        # for i in self.Connected_Port_Veri:
        #     i.disconnect()

        self.Listening_Port_Reg.stopListening()
        self.Listening_Port_Veri.stopListening()

        print("stopped listening on ports")
    # def run_protocol(self, protocol, data, cmd="write"):
    #     """
    #     must run with reactor.callFromThread
    #
    #     :param protocol: a connected instance of Twisted Protocol, should be connected to another verification node
    #     :param data: encoded(bytes) to write to connected protocol
    #     :param cmd: "write" or "end_con"
    #     :return: None
    #     """
    #
    #     if cmd == "end_con":
    #         protocol.loseConnection()
    #     else:
    #         protocol.write(data)





if __name__ == '__main__':
    pass




