from Orses_Administrator_Core.Administrator import Admin
from Orses_Network_Core.NetworkManager import NetworkManager
from Orses_Network_Messages_Core.NetworkPropagator import NetworkPropagator
from Orses_Network_Messages_Core.BlockchainPropagator import BlockChainPropagator
from Orses_Network_Core.NetworkMessageSorter import NetworkMessageSorter
from twisted.internet.error import CannotListenError

# for sandbox internet
from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyInternet
from Orses_Dummy_Network_Core.DummyAdminNode import DummyAdminNode

# https://superuser.com/questions/127863/manually-closing-a-port-from-commandline

from getpass import getpass
from twisted.internet import reactor, defer, threads

import sys, multiprocessing, queue, getopt, time

p_version = sys.version_info

assert (p_version.major >= 3 and p_version.minor >= 6), "must be running python 3.6.0 or greater\n" \
                                                        "goto www.python.org to install/upgrade"


# todo: update address list and omit including self address into known address list.
# todo: refactor name from propagator to network sorter in protocol/ factory

# todo: in send_token() and reserve_token() in Orses.py add a way of updating tokens and activities

# todo: create a test genesis block, block 1 and block 2. in block add some wallets that can be used

# todo: try to create a mock twisted protocol class, This class will receive message using a pipe, this
# todo: will be for testing internal testing of network propagation and validation.
# todo: This class then be used in a Start_virtual_node script which will allow for testing of certian functionaility


# todo: start competing/block creation process, finish up the blockchain process
# todo: Build a way to finish up any conversations with peers before ending program

# todo: protocol_id can conflict between VeriNodeConnector and VeriNodeListener. Make protocol id to increment when
# todo: either  is created.

# todo: work on validator for winning block

"""
file used to start node
1 load or create admin class
2. if admin.isCompetitor is None ask to create new competitor msg. if false, skip. if true, ask if would like compete
    
3 start Network Propagator, used to propagate validated network messages

4. start Network Listener and Validator process
"""


# loads or, if not yet created, creates new admin details. Also Creates the necessary database for running node
def send_stop_to_reactor(reactor_instance, q_object_to_each_node, dummy_internet=None,*args, **kwargs):
    """
    runs once the reactor is running, opens another thread that runs local function temp().
    This function waits for an exit signal, it then sends exit signal to other threads running, using the queue objects
    THese exit signals then trigger for other break off any loops and exit program


    :param reactor_instance, reactor instance from twisted reactor
    :param q_object_to_each_node: Queue object to send "exit" signal to each created node
    :param args: should be list of blocking objects: in this case q objects
    :param kwargs: option keywork argument of "number_of_nodes" can be passed
    :return:
    """
    print(args)
    number_of_nodes = kwargs["number_of_nodes"] if (
        "number_of_nodes" in kwargs and isinstance(kwargs["number_of_nodes"], int)
    ) else 0

    def temp():

        if reactor_instance.running:
            print("\nNode Started. To Stop Node Safely, type 'exit' or 'quit' without quote and press enter.\n")
            while True:
                ans = input("cmd: ").lower()

                if ans in {"exit", "quit"}:
                    for i in args:
                        if isinstance(i, (multiprocessing.Queue, queue.Queue)):
                            i.put(ans)
                    break
                elif ans == "print internet":
                    print("dummy internet instance: ",dummy_internet)
                    print("listening nodes: ",dummy_internet.listening_nodes)
                    print("addr to node: ", dummy_internet.address_to_node_dict)

            for i in range(number_of_nodes):
                q_object_to_each_node.put(ans)

            return ans


    # ******  THIS LINE IS IMPORTANT FOR CLEAN ENDING OF REACTOR ****** #
    # ****** THIS WAITS FOR EXIT SIGNAL AND THE FIRES CALLBACK WHICH RUNS reactor.stop() in the main thread ***** #
    response_thread = threads.deferToThread(temp)  # deffering blocking function to thread
    response_thread.addCallback(lambda x: reactor.stop())  # lambda function is fired when blocking function returns (and return anything)


def create_node_instances(dummy_internet, number_of_nodes_to_create: int, preferred_no_of_mining_nodes=0):
    assert number_of_nodes_to_create > 0, "number of admins to create must be at least 1"
    admins_list = list()
    nodes_dict ={
        "competing": [],
        "non-competing": []
    }
    while number_of_nodes_to_create:
        admins_list.append(Admin(
            admin_name=f'v{number_of_nodes_to_create}', password="xxxxxx", newAdmin=True, is_sandbox=True))
        number_of_nodes_to_create -= 1

    for _ in range(preferred_no_of_mining_nodes):  # creating competing nodes
        admin = admins_list.pop()
        admin.isCompetitor = True

        # create DummyAdminNode this automatically receives addr from dummy internet
        node = DummyAdminNode(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=reactor)
        nodes_dict["competing"].append(node)

    for admin in admins_list:
        node = DummyAdminNode(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=reactor)
        nodes_dict["non-competing"].append(node)

    return nodes_dict


def sandbox_main(number_of_nodes, reg_network_sandbox=False):
    """

    :param reg_network_sandbox: if false regular network will not be sandbox. This allows to send data to main node
    and then see how it reacts with the sandbox nodes
    :return:
    """

    # ThreadPool setup, 10 thread pools * number of node instances + 10 for main node:
    t_pool = reactor.getThreadPool()
    print(f"ThreadPool size is: {t_pool.max}")
    t_pool.adjustPoolsize(minthreads=0, maxthreads=int((number_of_nodes*15) + 15))
    print(f"ThreadPool size is: {reactor.getThreadPool().max}")

    print("You Are Running In Sandbox Mode")
    print("You will be able connect to the sandbox network using a regular client node and test by sending txs\n") if\
        reg_network_sandbox is False else \
        print("You will not be able to connect to the sandbox network and can only view automated interactions\n")

    admin_name = input("admin name: ")
    password = getpass("password: ")

    # admin loaded, if no admin by username, offer to create admin
    admin = Admin(admin_name=admin_name, password=password, newAdmin=False, is_sandbox=True).load_user()
    assert admin is not False, "Wrong Password"
    if admin is None:
        ans = input("No admin id under that admin name, would you like to create a new admin id? y/N ")
        if ans.lower() == "y":
            admin = Admin(admin_name=admin_name, password=password, newAdmin=True, is_sandbox=True)
        else:
            exit(0)
    print(admin)
    print(vars(admin))

    if admin.isCompetitor is True:
        compete = input("Start Competing? Y/n(default is Y)").lower()
        if compete in {"y", ""}:
            print("Competing Process Started...")
    elif admin.isCompetitor is None:
        compete = input("Would You like to compete to create blocks on the Orses Network?\n"
                        "press enter to skip, y for yes or n for no: ").lower()

        if compete == "y":
            print("\n a new competitor message will be sent to the network and included in the blockchain. \n"
                  "Once it has at least 10 confirmations. Blocks created by your node will be accepted by other "
                  "competitors and proxy nodes")
            admin.isCompetitor = True
            # todo: add logic to create new competitor network message for inclusion into the blockchain
        elif compete == "n":
            admin.isCompetitor = False

        else:  # sets compete to n for now and skps setting admin competitor status
            compete = 'n'
    else:
        compete = 'n'

    # instantiated Dummy Internet
    dummy_internet = DummyInternet()

    # instantiate main node
    main_node = DummyAdminNode(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=reactor)

    # *** instantiate queue variables ***
    q_for_compete = multiprocessing.Queue() if compete == 'y' else None
    q_for_validator = multiprocessing.Queue()
    q_for_propagate = multiprocessing.Queue()
    q_for_bk_propagate = multiprocessing.Queue()
    q_for_block_validator = multiprocessing.Queue()  # between block validators and block propagators
    q_for_initial_setup = multiprocessing.Queue()  # goes to initial setup
    q_object_from_protocol = multiprocessing.Queue()  # goes from protocol to message sorter
    q_object_to_each_node = multiprocessing.Queue()  # for exit signal

    # start compete(mining) process, if compete is yes. process is started using separate process (not just thread)
    if compete == 'y':
        pass

    # *** start blockchain propagator in different thread ***
    blockchain_propagator = BlockChainPropagator(
        q_object_connected_to_block_validator=q_for_block_validator,
        q_object_to_competing_process=q_for_compete,
        q_for_bk_propagate=q_for_bk_propagate,
        q_object_between_initial_setup_propagators=q_for_initial_setup,
        reactor_instance=main_node.reactor,  # use DummyReactor which implements real reactor.CallFromThread
        admin_instance=admin

    )

    # *** set intial setup to start in 3 seconds. This will get new blocks and data before other processes start ***
    reactor.callLater(3.0, blockchain_propagator.initial_setup)

    # *** start blockchain propagator manager in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_manager)

    # *** start blockchain propagator initiator in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_initiator)


    # *** Instantiate Network Propagator ***
    propagator = NetworkPropagator(
        q_object_connected_to_validator=q_for_validator,
        q_for_propagate=q_for_propagate,
        reactor_instance=main_node.reactor,
        q_object_between_initial_setup_propagators=q_for_initial_setup,
        is_sandbox=True,
        q_object_to_competing_process=q_for_compete,
        admin_inst=admin
    )

    # *** start propagator manager in another thread ***
    reactor.callInThread(propagator.run_propagator_convo_manager)

    # *** start propagator initiator in another thread ***
    reactor.callInThread(propagator.run_propagator_convo_initiator)

    # *** instantiate network message sorter ***
    network_message_sorter = NetworkMessageSorter(
        q_object_from_protocol,
        q_for_bk_propagate,
        q_for_propagate,
        node=main_node,
        b_propagator_inst=blockchain_propagator,
        n_propagator_inst=propagator
    )

    # *** start network manaager and run veri node factory and regular factory using reactor.callFromThread ***
    network_manager = NetworkManager(
        admin=admin,
        q_object_from_protocol=q_object_from_protocol,
        q_object_to_validator=q_for_validator,
        net_msg_sorter=network_message_sorter,
        reg_listening_port=55600,
        reg_network_sandbox=reg_network_sandbox
    )



    # *** run sorter in another thread ***
    reactor.callInThread(network_message_sorter.run_sorter)

    # *** use to connect to or listen for connection from other verification nodes ***
    reactor.callFromThread(
        network_manager.run_veri_node_network,
        main_node.reactor
    )

    # *** use to listen for connections from regular nodes ***
    if reg_network_sandbox is False:  # will run regular network with real reactor allowing outside client node testing
        reactor.callFromThread(
            network_manager.run_regular_node_network,
            reactor
        )
    else:  # will run regular network with dummy reactor for complete Sandbox testing
        reactor.callFromThread(
            network_manager.run_regular_node_network,
            main_node.reactor
        )

    # *** creates a deferral, which allows user to exit program by typing "exit" or "quit" ***
    reactor.callWhenRunning(
        send_stop_to_reactor,
        reactor,
        q_object_to_each_node,
        dummy_internet,
        q_for_propagate,
        q_for_bk_propagate,
        q_for_compete,
        q_object_from_protocol,
        q_for_validator,
        q_for_block_validator,
        number_of_nodes=number_of_nodes
    )

    # *** set propagator's network manager variable to network manager instance ***
    propagator.network_manager = network_manager

    # **** CREATE OTHER NODE INSTANCES **** #

    node_dict = create_node_instances(
        dummy_internet=dummy_internet,
        number_of_nodes_to_create=number_of_nodes,
        preferred_no_of_mining_nodes=0
    )

    for temp_node in node_dict["competing"]:

        reactor.callInThread(

            temp_node.run_node,
            real_reactor_instance=reactor,
            q_object_to_each_node=q_object_to_each_node,
            reg_network_sandbox=True

        )

    for temp_node in node_dict["non-competing"]:
        reactor.callInThread(

            temp_node.run_node,
            real_reactor_instance=reactor,
            q_object_to_each_node=q_object_to_each_node,
            reg_network_sandbox=True

        )


    # *** start reactor ***
    reactor.run()

    # *** This will only print when reactor is stopped
    print("Node Stopped")

    # *** when reactor is stopped save admin details ***
    admin.save_admin()


def main():

    # input admin name and password
    admin_name = input("admin name: ")
    password = getpass("password: ")

    # admin loaded, if no admin by username, offer to create admin
    admin = Admin(admin_name=admin_name, password=password, newAdmin=False, is_sandbox=False).load_user()
    assert admin is not False, "Wrong Password"
    if admin is None:
        ans = input("No admin id under that admin name, would you like to create a new admin id? y/N ")
        if ans.lower() == "y":
            admin = Admin(admin_name=admin_name, password=password, newAdmin=True, is_sandbox=False)
        else:
            exit(0)

    print(admin)
    print(vars(admin))

    # Start competing process if admin.isCompetitor == True
    if admin.isCompetitor is True:
        compete = input("Start Competing? Y/n(default is Y)").lower()
        if compete in {"y", ""}:
            print("Competing Process Started...")
    elif admin.isCompetitor is None:
        compete = input("Would You like to compete to create blocks on the Orses Network?\n"
                        "press enter to skip, y for yes or n for no: ").lower()

        if compete == "y":
            print("\n a new competitor message will be sent to the network and included in the blockchain. \n"
                  "Once it has at least 10 confirmations. Blocks created by your node will be accepted by other "
                  "competitors and proxy nodes")
            admin.isCompetitor = True
            # todo: add logic to create new competitor network message for inclusion into the blockchain
        elif compete == "n":
            admin.isCompetitor = False

        else:  # sets compete to n for now and skps setting admin competitor status
            compete = 'n'
    else:
        compete = 'n'

    # *** instantiate queue variables ***
    q_for_compete = multiprocessing.Queue() if compete == 'y' else None
    q_for_validator = multiprocessing.Queue()
    q_for_propagate = multiprocessing.Queue()
    q_for_bk_propagate = multiprocessing.Queue()
    q_for_block_validator = multiprocessing.Queue()  # between block validators and block propagators
    q_for_initial_setup = multiprocessing.Queue()  # goes to initial setup
    q_object_from_protocol = multiprocessing.Queue()  # goes from protocol to message sorter
    q_object_to_each_node = multiprocessing.Queue()  # for exit signal

    # start compete(mining) process, if compete is yes. process is started using separate process (not just thread)
    if compete == 'y':
        pass

    # *** start blockchain propagator in different thread ***
    blockchain_propagator = BlockChainPropagator(
        q_object_connected_to_block_validator=q_for_block_validator,
        q_object_to_competing_process=q_for_compete,
        q_for_bk_propagate=q_for_bk_propagate,
        q_object_between_initial_setup_propagators=q_for_initial_setup,
        reactor_instance=reactor,
        admin_instance=admin

    )

    # *** set intial setup to start in 3 seconds. This will get new blocks and data before other processes start ***
    reactor.callLater(3.0, blockchain_propagator.initial_setup)

    # *** start blockchain propagator manager in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_manager)

    # *** start blockchain propagator initiator in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_initiator)

    # *** Instantiate Network Propagator ***
    propagator = NetworkPropagator(
        q_object_connected_to_validator=q_for_validator,
        q_for_propagate=q_for_propagate,
        reactor_instance=reactor,
        q_object_between_initial_setup_propagators=q_for_initial_setup,
        is_sandbox=False,
        q_object_to_competing_process=q_for_compete,
        admin_inst=admin
    )

    # *** start propagator manager in another thread ***
    reactor.callInThread(propagator.run_propagator_convo_manager)

    # *** start propagator initiator in another thread ***
    reactor.callInThread(propagator.run_propagator_convo_initiator)

    # *** start network manaager and run veri node factory and regular factory using reactor.callFromThread ***
    network_manager = NetworkManager(
        admin=admin,
        q_object_from_protocol=q_object_from_protocol,
        q_object_to_validator=q_for_validator,
        net_msg_sorter=propagator,
        reg_listening_port=55600,
        reg_network_sandbox=False
    )

    # *** instantiate network message sorter ***
    network_message_sorter = NetworkMessageSorter(q_object_from_protocol, q_for_bk_propagate, q_for_propagate)

    # *** run sorter in another thread ***
    reactor.callInThread(network_message_sorter.run_sorter)


    # *** use to connect to and listen for connection from other verification nodes ***
    reactor.callFromThread(
        network_manager.run_veri_node_network,
        reactor
    )

    # *** use to listen for connections from regular nodes ***
    reactor.callFromThread(
        network_manager.run_regular_node_network,
        reactor
    )




    # *** creates a deferral, which allows user to exit program by typing "exit" or "quit" ***
    reactor.callWhenRunning(
        send_stop_to_reactor,
        reactor,
        q_object_to_each_node,
        None,
        q_for_propagate,
        q_for_bk_propagate,
        q_for_compete,
        q_object_from_protocol,
        q_for_validator,
        q_for_block_validator,

    )

    # *** set propagator's network manager variable to network manager instance ***
    propagator.network_manager = network_manager

    # *** start reactor ***
    reactor.run()

    # *** This will only print when reactor is stopped
    print("Node Stopped")

    # *** when reactor is stopped save admin details ***
    admin.save_admin()


if __name__ == '__main__':
    sandbox_main(number_of_nodes=1, reg_network_sandbox=False)

    # long_opt = ["sandbox"]
    # short_opt = "s"
    #
    # try:
    #     optlist, args = getopt.getopt(sys.argv[1:], shortopts=short_opt, longopts=long_opt)
    #
    # except getopt.GetoptError as e:
    #     print(e)
    #     print("only option available is -s or --sandbox, both will run sandbox network for testing")
    # else:
    #
    #     if optlist:  # only option available is sandbox
    #         try:
    #             print("Starting Sandbox Network")
    #             print("Network only for testing on local computer...")
    #             time.sleep(2)
    #             sandbox_main()
    #         except (SystemExit, KeyboardInterrupt) as e:
    #             if reactor.running:
    #                 reactor.stop()
    #             print(e)
    #     else:
    #         try:
    #             print("Starting Node....")
    #
    #             main()
    #         except (SystemExit, KeyboardInterrupt) as e:
    #             if reactor.running:
    #                 reactor.stop()
    #             print(e)








