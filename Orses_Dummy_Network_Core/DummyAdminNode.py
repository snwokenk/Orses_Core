
from twisted.internet import reactor, defer, threads
from Orses_Network_Messages_Core.BlockchainPropagator import BlockChainPropagator
from Orses_Network_Messages_Core.NetworkPropagator import NetworkPropagator
from Orses_Network_Core.NetworkManager import NetworkManager
from Orses_Network_Core.NetworkMessageSorter import NetworkMessageSorter
from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyNode

import multiprocessing, queue, shutil, os


class DummyAdminNode(DummyNode):
    """
    mimic an admin node
    """

    def __init__(self, admin,  dummy_internet, real_reactor_instance):

        super().__init__(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=real_reactor_instance)

        self.new_admin = admin.isNewAdmin
        self.is_competitor = admin.isCompetitor
        self.copy_important_files()

    def copy_important_files(self):
        path_of_main = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Default_Addresses_Sandbox")
        try:
            shutil.copy(path_of_main, self.admin.fl.get_username_folder_path())
        except FileExistsError:
            print("In DummyAdminNode.py, copy_important_files(): Default_Addresses_Sandbox file already exists")

    def send_stop_to_reactor(self, q_object_to_each_node, *args):
        """
        runs once the reactor is running, opens another thread that runs local function temp().
        This function waits for an exit signal, it then sends exit signal to other threads running, using the queue objects
        THese exit signals then trigger for other break off any loops and exit program

        :param q_object_to_each_node: Queue object to receive exit signal
        :param args: should be list of blocking objects: in this case q objects
        :return:
        """
        # print(args)

        # wait for signal
        q_object_to_each_node.get()

        if self.reactor.running:
            for i in args:
                if isinstance(i, (multiprocessing.Queue, queue.Queue)):
                    i.put("exit")

            self.reactor.stop()



        #             # ******  THIS LINE IS IMPORTANT FOR CLEAN ENDING OF REACTOR ****** #
        # # ****** THIS WAITS FOR EXIT SIGNAL AND THE FIRES CALLBACK WHICH RUNS reactor.stop() in the main thread ***** #
        # response_thread = threads.deferToThread(temp)  # deffering blocking function to thread
        # response_thread.addCallback(lambda x: print(f"{self.admin.admin_name} is Stopped"))

    def run_node(self, real_reactor_instance, q_object_to_each_node: multiprocessing.Queue, reg_network_sandbox=True):
        """
        Run node
        :param reg_network_sandbox: if regular client network should be run in sandbox also
        :param real_reactor_instance: this is an instance of reactor from Twisted framework. NOT THE DUMMYREACTOR!
        :param q_object_to_each_node: multiprocessing.Queue object for sending exit signal to each node
        :return:
        """

        # *** instantiate queue variables ***
        q_for_compete = multiprocessing.Queue() if self.is_competitor == 'y' else None
        q_for_validator = multiprocessing.Queue()
        q_for_propagate = multiprocessing.Queue()
        q_for_bk_propagate = multiprocessing.Queue()
        q_for_block_validator = multiprocessing.Queue()  # between block validators and block propagators
        q_for_initial_setup = multiprocessing.Queue()  # goes to initial setup
        q_object_from_protocol = multiprocessing.Queue()  # goes from protocol to message sorter

        # start compete(mining) process, if compete is yes. process is started using separate process (not just thread)
        if self.is_competitor == 'y':
            pass

        # *** start blockchain propagator in different thread ***
        blockchain_propagator = BlockChainPropagator(
            q_object_connected_to_block_validator=q_for_block_validator,
            q_object_to_competing_process=q_for_compete,
            q_for_bk_propagate=q_for_bk_propagate,
            q_object_between_initial_setup_propagators=q_for_initial_setup,
            reactor_instance=self.reactor,  # use DummyReactor which implements real reactor.CallFromThread
            admin_instance=self.admin

        )

        # *** set intial setup to start in 3 seconds. This will get new blocks and data before other processes start ***
        self.reactor.callLater(3.0, blockchain_propagator.initial_setup)

        # *** start blockchain propagator manager in separate thread ***
        self.reactor.callInThread(blockchain_propagator.run_propagator_convo_manager)

        # *** start blockchain propagator initiator in separate thread ***
        self.reactor.callInThread(blockchain_propagator.run_propagator_convo_initiator)

        propagator = NetworkPropagator(
            q_object_connected_to_validator=q_for_validator,
            q_for_propagate=q_for_propagate,
            reactor_instance=self.reactor,
            q_object_between_initial_setup_propagators=q_for_initial_setup,
            is_sandbox=True,
            q_object_to_competing_process=q_for_compete,
            admin_inst=self.admin
        )

        # *** start propagator manager in another thread ***
        self.reactor.callInThread(propagator.run_propagator_convo_manager)

        # *** start propagator initiator in another thread ***
        self.reactor.callInThread(propagator.run_propagator_convo_initiator)

        # *** start network manaager and run veri node factory and regular factory using reactor.callFromThread ***
        network_manager = NetworkManager(
            admin=self.admin,
            q_object_from_protocol=q_object_from_protocol,
            q_object_to_validator=q_for_validator,
            propagator=propagator,
            reg_listening_port=55600,
            reg_network_sandbox=reg_network_sandbox
        )


        # *** instantiate network message sorter ***
        network_message_sorter = NetworkMessageSorter(
            q_object_from_protocol,
            q_for_bk_propagate,
            q_for_propagate,
            node=self
        )

        # *** run sorter in another thread ***
        self.reactor.callInThread(network_message_sorter.run_sorter)

        # *** use to connect to or listen for connection from other verification nodes ***

        self.reactor.callInThread(
            network_manager.run_veri_node_network,
            self.reactor
        )


        # *** use to listen for connections from regular nodes ***
        if reg_network_sandbox is False:  # will run regular network with real reactor allowing outside client node testing
            reactor.callFromThread(
                network_manager.run_regular_node_network,
                real_reactor_instance
            )
        else:  # will run regular network with dummy reactor for complete Sandbox testing
            self.reactor.callInThread(
                network_manager.run_regular_node_network,
                self.reactor
            )

        # *** set propagator's network manager variable to network manager instance ***
        propagator.network_manager = network_manager
        self.reactor.run()

        self.reactor.callInThread(
            self.send_stop_to_reactor,
            q_object_to_each_node,
            q_for_propagate,
            q_for_bk_propagate,
            q_for_compete,
            q_object_from_protocol,
            q_for_validator,
            q_for_block_validator

        )

