
from twisted.internet import reactor, defer, threads
from Orses_Network_Messages_Core.BlockchainPropagator import BlockChainPropagator
from Orses_Network_Messages_Core.NetworkPropagator import NetworkPropagator
from Orses_Network_Messages_Core.MemPool import MemPool
from Orses_Network_Core.NetworkManager import NetworkManager
from Orses_Network_Core.NetworkMessageSorter import NetworkMessageSorter
from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyNode
from Orses_Competitor_Core.Orses_Compete_Algo import Competitor
from Orses_Database_Core.OrsesLevelDBManagement import OrsesLevelDBManager


import multiprocessing, queue, shutil, os, time, threading


class DummyAdminNode(DummyNode):
    """
    mimic an admin node
    """

    nodeID = 0

    def __init__(self, admin,  dummy_internet, real_reactor_instance, is_program_running):

        super().__init__(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=real_reactor_instance)
        self.node_id = DummyAdminNode.nodeID
        DummyAdminNode.nodeID+=1
        self.new_admin = admin.isNewAdmin
        self.is_competitor = admin.isCompetitor
        self.copy_important_files()
        self.q_for_compete = multiprocessing.Queue() if self.is_competitor is True else None
        self.q_for_validator = multiprocessing.Queue()
        self.q_for_bk_propagate = multiprocessing.Queue()
        self.q_object_from_compete_process_to_mining = multiprocessing.Queue()
        self.q_for_block_validator = multiprocessing.Queue()
        self.is_generating_block = multiprocessing.Event()
        self.has_received_new_block = multiprocessing.Event()
        self.is_program_running = is_program_running
        self.competitor = Competitor(
            reward_wallet="Wf693c7655fa6c49b3b28e2ac3394944c43d369cc",
            admin_inst=self.admin,
            is_program_running=is_program_running
        )

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
                if isinstance(i, (multiprocessing.queues.Queue, queue.Queue)):
                    i.put("exit")

            self.reactor.stop()



        #             # ******  THIS LINE IS IMPORTANT FOR CLEAN ENDING OF REACTOR ****** #
        # # ****** THIS WAITS FOR EXIT SIGNAL AND THE FIRES CALLBACK WHICH RUNS reactor.stop() in the main thread ***** #
        # response_thread = threads.deferToThread(temp)  # deffering blocking function to thread
        # response_thread.addCallback(lambda x: print(f"{self.admin.admin_name} is Stopped"))

    def run_mining_thread_for_dummyNode(self):
        if self.admin.isCompetitor is True:

            self.reactor.callInThread(
                self.competitor.handle_new_block,
                q_object_from_compete_process_to_mining=self.q_object_from_compete_process_to_mining,
                q_for_block_validator=self.q_for_block_validator,
                is_generating_block=self.is_generating_block,
                has_received_new_block=self.has_received_new_block
            )

    def run_compete_thread(self):

        if self.admin.isCompetitor is True:

            self.reactor.callInThread(
                self.competitor.compete,
                q_for_compete=self.q_for_compete,
                q_object_from_compete_process_to_mining=self.q_object_from_compete_process_to_mining,
                is_generating_block=self.is_generating_block,
                has_received_new_block=self.has_received_new_block

            )

            # run the mining thread, main node will use multiprocessing but dummy nodes use threads
            self.run_mining_thread_for_dummyNode()

            return True

    def run_node(self, real_reactor_instance, q_object_to_each_node: multiprocessing.Queue, reg_network_sandbox=True, compete_process=None):
        """
        Run node
        :param reg_network_sandbox: if regular client network should be run in sandbox also
        :param real_reactor_instance: this is an instance of reactor from Twisted framework. NOT THE DUMMYREACTOR!
        :param q_object_to_each_node: multiprocessing.Queue object for sending exit signal to each node
        :return:
        """

        # this will wait for 6 seconds allowing main node to setup
        if self.node_id:
            time.sleep(6 + self.node_id)

        # *** instantiate queue variables ***
        q_for_compete = self.q_for_compete
        q_for_validator = self.q_for_validator
        q_for_propagate = multiprocessing.Queue()
        q_for_bk_propagate = self.q_for_bk_propagate
        q_for_block_validator = self.q_for_block_validator  # between block validators and block propagators
        q_for_initial_setup = multiprocessing.Queue()  # goes to initial setup
        q_object_from_protocol = multiprocessing.Queue()  # goes from protocol to message sorter
        q_object_from_compete_process_to_mining = self.q_object_from_compete_process_to_mining

        # instantiate a levelDB manager class,
        # add to admin (easier to do since admin instance is found in almost every class and process)
        db_manager = OrsesLevelDBManager(admin_inst=self.admin)
        db_manager.load_required_databases()

        self.admin.load_db_manager(db_manager=db_manager)

        # start compete(mining) process, if admin.isCompetitor is True. No need to check compete for virtual node
        print(f"in DummyAdminNode, is admin competitor {self.admin.isCompetitor}")

        mempool = MemPool(admin_inst=self.admin)
        self.admin.load_mempool_instance(mempool_inst=mempool)

        def callback_non_compete(prev_block):
            reactor.callInThread(
                self.competitor.non_compete_process,
                q_for_block_validator=q_for_block_validator,
                reactor_inst=self.reactor,
                last_block=prev_block
            )

        if self.admin.isCompetitor is True:
            try:
                is_alive = compete_process.is_alive()
            except AttributeError:
                is_alive = False
            print(f"Compete Prcess Should Have Started In Main Thread (coded on start_node.py), "
                  f"Process_is_alive {is_alive}")

        # *** start blockchain propagator in different thread ***
        blockchain_propagator = BlockChainPropagator(
            mempool=mempool,
            q_object_connected_to_block_validator=q_for_block_validator,
            q_object_to_competing_process=q_for_compete,
            q_for_bk_propagate=q_for_bk_propagate,
            q_object_between_initial_setup_propagators=q_for_initial_setup,
            reactor_instance=self.reactor,  # use DummyReactor which implements real reactor.CallFromThread
            admin_instance=self.admin,
            is_program_running=self.is_program_running

        )

        # *** set intial setup to start in 3 seconds. This will get new blocks and data before other processes start ***
        self.reactor.callLater(3.0, blockchain_propagator.initial_setup, callback_non_compete)

        # *** start blockchain propagator manager in separate thread ***
        self.reactor.callInThread(blockchain_propagator.run_propagator_convo_manager)

        # *** start blockchain propagator initiator in separate thread ***
        self.reactor.callInThread(blockchain_propagator.run_propagator_convo_initiator)

        propagator = NetworkPropagator(
            mempool=mempool,
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

        # *** instantiate network message sorter ***
        network_message_sorter = NetworkMessageSorter(
            q_object_from_protocol,
            q_for_bk_propagate,
            q_for_propagate,
            node=self,
            b_propagator_inst=blockchain_propagator,
            n_propagator_inst=propagator
        )

        # *** start network manaager and run veri node factory and regular factory using reactor.callFromThread ***
        network_manager = NetworkManager(
            admin=self.admin,
            q_object_from_protocol=q_object_from_protocol,
            q_object_to_validator=q_for_validator,
            net_msg_sorter=network_message_sorter,
            reg_listening_port=55600,
            reg_network_sandbox=reg_network_sandbox,
            reactor_inst=self.reactor
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

        db_manager.create_load_wallet_balances_from_genesis_block()



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


