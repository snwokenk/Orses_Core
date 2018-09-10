from Orses_Administrator_Core.Administrator import Admin
from Orses_Network_Core.NetworkManager import NetworkManager
from Orses_Network_Messages_Core.NetworkPropagator import NetworkPropagator
from Orses_Network_Messages_Core.BlockchainPropagator import BlockChainPropagator
from Orses_Network_Messages_Core.MemPool import MemPool
from Orses_Network_Core.NetworkMessageSorter import NetworkMessageSorter
from Orses_Competitor_Core.Orses_Compete_Algo import Competitor

from twisted.internet.error import CannotListenError

# for sandbox internet
from Orses_Dummy_Network_Core.DummyNetworkObjects import DummyInternet
from Orses_Dummy_Network_Core.DummyAdminNode import DummyAdminNode

# https://superuser.com/questions/127863/manually-closing-a-port-from-commandline
# 'sudo netstat -ap | grep :<port_number>' to get process id owning port then 'kill <pid>' to kill process

# using git: http://rogerdudler.github.io/git-guide/
# https://stackoverflow.com/questions/19924104/python-multiprocessing-handling-child-errors-in-parent
# https://docs.quantifiedcode.com/python-anti-patterns/index.html
# https://opensource.guide/starting-a-project/
# https://bitcoin.stackexchange.com/questions/10821/how-long-does-it-take-to-propagate-a-newly-created-block-to-the-entire-bitcoin-n

from getpass import getpass
from twisted.internet import reactor, defer, threads

from pkg_resources import DistributionNotFound, VersionConflict

import sys, multiprocessing, queue, getopt, time, pkg_resources
from multiprocessing import synchronize
from multiprocessing.queues import Queue

p_version = sys.version_info

assert (p_version.major >= 3 and p_version.minor >= 6), "must be running python 3.6.0 or greater\n" \
                                                        "goto www.python.org to install/upgrade"

# check all dependencies from requirements.txt is installed
try:
    with open("requirements.txt", "r") as f:
        dependencies = f.readlines()
    pkg_resources.require(dependencies)
except DistributionNotFound as e:
    print(e)
    print("open a command/terminal window and type 'pip install -r requirements.txt' ")
    exit()
except VersionConflict as ee:
    print(ee)
    print("open a command/terminal window and type 'pip install -r requirements.txt' ")
    exit()

else:
    print("All Required Packages Installed")


# todo: allow non-competitors to still run run_block_winner_chooser_process and check_winning_block_from_network


# todo: bitcoin propagation takes roughly 1 minute for a propagation of 95%. Will have to increase wait time to 45 secs

# todo: Refactor ttx or rsv_req validators to search blocks and verify enough tokens are unspent for transaction
# todo: create a block validator which validates newly created block from others
# todo: this validator first checks that transactions in the block are part of its validated transactions
# todo: those that are not a independently verified before block is accepted by node
# todo: this process of validation should keep track of the winning block and the


# todo: might do away with a separate secondary signatories section for block 1 and above, just add to misc_messages or reward
# todo: in order to speed up merkle root creation, propagation and verification, dicts might be turned to list
# todo: when adding transactions etc to new block, verify it hasn't been added to prev block(not in merkle root)

# todo: in compete() of Competitor class, figure out how to add store txs, wallet state hashes and misc msgs before
# todo: block is created. This process should allow creation of empty dicts at start of a round and populate them
# todo: during a round. The dict can be divided into fees, time etc


# todo: token amounts should be represented in the smallest unit of Orses tokens or 'ntakiris'
# todo: with 1 orses token == 10,000,000,000 (10 billion) ntakiris

# todo: even though multiprocessing is being used to to use twisted's Process Protocol
# todo: https://twistedmatrix.com/documents/current/core/howto/process.html


# todo: delete the many print statements in BlockchainPropagator.py
# todo: before doing compete algo, finish initial setup, by adding code to convo_manager of blockchainPropagator
# todo: finish compete algo
# todo: finish block_data_aggregator set_maximum_probability_target
# todo: create a test genesis block, block 1 and block 2. in gen block add some wallets that can be used
# todo: work on validator for winning block. A block is passed through this validator
# todo: create a class or dictionary that holds potential winning blocks and is used by validator.
# todo: The final winning block, resets this class or dictionary

# todo: implement error logging, when message received causes error. for now print error and msg
# todo: start competing/block creation process, finish up the blockchain process.
# todo: Refactor Assignment statement, Token Transfer, Token Reservation Validators to check blockchain for proof of tokens


# todo: Build a way to finish up any conversations with peers before ending program


# todo: in send_token() and reserve_token() in Orses.py add a way of updating tokens and activities

"""
file used to start node
1 load or create admin class
2. if admin.isCompetitor is None ask to create new competitor msg. if false, skip. if true, ask if would like compete
    
3 start Network Propagator, used to propagate validated network messages

4. start Network Listener and Validator process
"""


# loads or, if not yet created, creates new admin details. Also Creates the necessary database for running node
def send_stop_to_reactor(reactor_instance, q_object_to_each_node, is_program_running: multiprocessing.synchronize.Event,
                         is_not_in_process_of_creating_new_block: multiprocessing.synchronize.Event, dummy_internet=None, *args, **kwargs):
    """
    runs once the reactor is running, opens another thread that runs local function temp().
    This function waits for an exit signal, it then sends exit signal to other threads running, using the queue objects
    THese exit signals then trigger for other break off any loops and exit program


    :param reactor_instance, reactor instance from twisted reactor
    :param q_object_to_each_node: Queue object to send "exit" signal to each created node
    :param is_program_running: a multiprocessing.Event object which is set to true at beginning of program
            and set to false by this function. This event is used by while loops (mining loops etc) that do not use a
            queue object or do but with a timeout
    :param is_in_process_of_creating_new_block: used to check if local node is in process of creating block
            This is used to exit the program after a choice of new block has been made and before new mining
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

                print(f"is_not_in_process_of_creating_new_block {is_not_in_process_of_creating_new_block.is_set()}")

                if ans in {"exit", "quit"}:

                    if not is_not_in_process_of_creating_new_block.is_set():
                        print(f"*** Node Currently In New Block Creation Process ***")
                        print(f"Waiting For Block Winner To Be Chosen")
                        is_not_in_process_of_creating_new_block.wait()

                    is_program_running.clear()
                    for i in args:
                        if isinstance(i, (multiprocessing.queues.Queue, queue.Queue)):
                            i.put(ans)
                    break
                elif dummy_internet is not None and ans == "print internet":
                    print("dummy internet instance: ",dummy_internet)
                    print("listening nodes: ",dummy_internet.listening_nodes)
                    print("addr to node: ", dummy_internet.address_to_node_dict)

            for i in range(number_of_nodes):  # number of nodes is 0, if running on real network
                q_object_to_each_node.put(ans)

            return ans


    # ******  THIS LINE IS IMPORTANT FOR CLEAN ENDING OF REACTOR ****** #
    # ****** THIS WAITS FOR EXIT SIGNAL AND THE FIRES CALLBACK WHICH RUNS reactor.stop() in the main thread ***** #
    response_thread = threads.deferToThread(temp)  # deffering blocking function to thread
    response_thread.addCallback(lambda x: reactor.stop())  # lambda function is fired when blocking function returns (and return anything)
    response_thread.addErrback(lambda x: print(x))


def create_node_instances(dummy_internet, number_of_nodes_to_create: int, is_program_running, preferred_no_of_mining_nodes=0, ):
    """

    :param dummy_internet:
    :param number_of_nodes_to_create:
    :param preferred_no_of_mining_nodes: number of mining nodes from nodes created
    :param genesis_start: tells competing node to start create block 1 without waiting for blocks.
    (only block available should be block 0 aka genesis block)
    :return:
    """
    assert number_of_nodes_to_create > 0, "number of admins to create must be at least 1"
    assert number_of_nodes_to_create >= preferred_no_of_mining_nodes, "number of mining nodes should be less than or " \
                                                                      "equal to number of created nodes"

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
        node = DummyAdminNode(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=reactor,
                              is_program_running=is_program_running)
        nodes_dict["competing"].append(node)

    for admin in admins_list:
        node = DummyAdminNode(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=reactor,
                              is_program_running=is_program_running)
        nodes_dict["non-competing"].append(node)

    return nodes_dict


def sandbox_main(number_of_nodes: int, reg_network_sandbox=False, preferred_no_of_mining_nodes=0, just_launched=True):
    """
    :param number_of_nodes: number of dummy nodes to create + main node for user
    :param reg_network_sandbox: if false regular network will not be sandbox. This allows to send data to main node
    and then see how it reacts with the sandbox nodes
    :param preferred_no_of_mining_nodes: number of mining nodes out of created nodes must be =< number of nodes
    :param just_launched: tells node just launched and to start immediately mining
    :return:
    """

    # set to false by exit process, which signals other processes to end (exit also sends an 'exit' or 'quit'
    is_program_running = multiprocessing.Event()
    is_program_running.set()
    print("program is running?", is_program_running.is_set())

    # used set to true when block mining and then to false after block winner has been chosen
    # used by exit process, to avoid stopping program in the middle of this process.
    # which can result in a loss of value
    is_not_in_process_of_creating_new_block = multiprocessing.Event()



    assert number_of_nodes >= preferred_no_of_mining_nodes, "number of mining nodes should be less than or equal " \
                                                            "to number of created nodes"
    # ThreadPool setup, 15 thread pools * number of node instances + 15 for main node:
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
    main_node = DummyAdminNode(admin=admin, dummy_internet=dummy_internet, real_reactor_instance=reactor,
                               is_program_running=is_program_running)

    # *** instantiate queue variables ***
    q_for_compete = multiprocessing.Queue() if (admin.isCompetitor is True and compete == 'y') else None
    q_for_validator = multiprocessing.Queue()
    q_for_propagate = multiprocessing.Queue()
    q_for_bk_propagate = multiprocessing.Queue()
    q_for_block_validator = multiprocessing.Queue()  # between block validators and block propagators
    q_for_initial_setup = multiprocessing.Queue()  # goes to initial setup
    q_object_from_protocol = multiprocessing.Queue()  # goes from protocol to message sorter
    q_object_to_each_node = multiprocessing.Queue()  # for exit signal
    q_object_from_compete_process_to_mining = multiprocessing.Queue()  # q between compete_process and handle_new_block

    # instantiate mempool object
    mempool = MemPool(admin_inst=admin)

    # start compete(mining) process, if compete is yes. process is started using separate process (not just thread)
    if admin.isCompetitor is True and compete == 'y':

        # multiprocessing event objects
        is_generating_block = multiprocessing.Event()
        has_received_new_block = multiprocessing.Event()

        # instantiate the competitor class
        competitor = Competitor(
            reward_wallet="W884c07be004ee2a8bc14fb89201bbc607e75258d",
            admin_inst=admin,
            is_program_running=is_program_running,
            just_launched=just_launched,
        )

        # start compete thread using twisted reactor's thread
        reactor.callInThread(
            competitor.compete,
            q_for_compete=q_for_compete,
            q_object_from_compete_process_to_mining=q_object_from_compete_process_to_mining,
            is_generating_block=is_generating_block,
            has_received_new_block=has_received_new_block,
            is_not_in_process_of_creating_new_block=is_not_in_process_of_creating_new_block

        )

        # start process for actual hashing
        p = multiprocessing.Process(
            target=competitor.handle_new_block,
            kwargs={
                "q_object_from_compete_process_to_mining": q_object_from_compete_process_to_mining,
                "q_for_block_validator": q_for_block_validator,
                "is_generating_block": is_generating_block,
                "has_received_new_block": has_received_new_block,
                "is_program_running": is_program_running,
                "is_not_in_process_of_creating_new_block": is_not_in_process_of_creating_new_block

            }

        )

        p.daemon = False
        p.start()


    # *** start blockchain propagator in different thread ***
    blockchain_propagator = BlockChainPropagator(
        mempool=mempool,
        q_object_connected_to_block_validator=q_for_block_validator,
        q_object_to_competing_process=q_for_compete,
        q_for_bk_propagate=q_for_bk_propagate,
        q_object_between_initial_setup_propagators=q_for_initial_setup,
        reactor_instance=main_node.reactor,  # use DummyReactor which implements real reactor.CallFromThread
        admin_instance=admin,
        is_program_running=is_program_running

    )

    # *** set intial setup to start in 3 seconds. This will get new blocks and data before other processes start ***
    reactor.callLater(3.0, blockchain_propagator.initial_setup)

    # *** start blockchain propagator manager in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_manager)

    # *** start blockchain propagator initiator in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_initiator)


    # *** Instantiate Network Propagator ***
    propagator = NetworkPropagator(
        mempool=mempool,
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
        is_program_running,
        is_not_in_process_of_creating_new_block,
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
        preferred_no_of_mining_nodes=preferred_no_of_mining_nodes,
        is_program_running=is_program_running
    )

    # separate processes are created for competing nodes in the Main thread, these processes will wait for most
    # recent block to be sent before starting to actually compete.

    for temp_node in node_dict["competing"]:

        node_compete_process = temp_node.run_compete_thread()

        reactor.callInThread(

            temp_node.run_node,
            real_reactor_instance=reactor,
            q_object_to_each_node=q_object_to_each_node,
            reg_network_sandbox=True,
            compete_process=node_compete_process

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


def main(just_launched=False):
    # set to false by exit process, which signals other processes to end (exit also sends an 'exit' or 'quit'
    is_program_running = multiprocessing.Event()
    is_program_running.set()
    print("program is running?", is_program_running.is_set())

    # used set to true when block mining and then to false after block winner has been chosen
    # used by exit process, to avoid stopping program in the middle of this process.
    # which can result in a loss of value
    is_not_in_process_of_creating_new_block = multiprocessing.Event()

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
    q_for_compete = multiprocessing.Queue() if (admin.isCompetitor is True and compete == 'y') else None
    q_for_validator = multiprocessing.Queue()
    q_for_propagate = multiprocessing.Queue()
    q_for_bk_propagate = multiprocessing.Queue()
    q_for_block_validator = multiprocessing.Queue()  # between block validators and block propagators
    q_for_initial_setup = multiprocessing.Queue()  # goes to initial setup
    q_object_from_protocol = multiprocessing.Queue()  # goes from protocol to message sorter
    q_object_from_compete_process_to_mining = multiprocessing.Queue()  # q between compete_process and handle_new_block


    # instantiate mempool object
    mempool = MemPool(admin_inst=admin)

    # start compete(mining) process, if compete is yes. process is started using separate process (not just thread)
    if admin.isCompetitor is True and compete == 'y':
        # multiprocessing event objects
        is_generating_block = multiprocessing.Event()
        has_received_new_block = multiprocessing.Event()

        # instantiate the competitor class
        competitor = Competitor(
            reward_wallet="W884c07be004ee2a8bc14fb89201bbc607e75258d",
            admin_inst=admin,
            just_launched=just_launched,
            is_program_running=is_program_running
        )

        # start compete thread using twisted reactor's thread
        reactor.callInThread(
            competitor.compete,
            q_for_compete=q_for_compete,
            q_object_from_compete_process_to_mining=q_object_from_compete_process_to_mining,
            is_generating_block=is_generating_block,
            has_received_new_block=has_received_new_block,
            is_not_in_process_of_creating_new_block=is_not_in_process_of_creating_new_block

        )

        # start process for actual hashing
        p = multiprocessing.Process(
            target=competitor.handle_new_block,
            kwargs={
                "q_object_from_compete_process_to_mining": q_object_from_compete_process_to_mining,
                "q_for_block_validator": q_for_block_validator,
                "is_generating_block": is_generating_block,
                "has_received_new_block": has_received_new_block,
                "is_program_running": is_program_running,
                "is_not_in_process_of_creating_new_block": is_not_in_process_of_creating_new_block

            }

        )

        p.daemon = True
        p.start()

    # *** start blockchain propagator in different thread ***
    blockchain_propagator = BlockChainPropagator(
        mempool=mempool,
        q_object_connected_to_block_validator=q_for_block_validator,
        q_object_to_competing_process=q_for_compete,
        q_for_bk_propagate=q_for_bk_propagate,
        q_object_between_initial_setup_propagators=q_for_initial_setup,
        reactor_instance=reactor,
        admin_instance=admin,
        is_program_running=is_program_running


    )

    # *** set intial setup to start in 3 seconds. This will get new blocks and data before other processes start ***
    reactor.callLater(3.0, blockchain_propagator.initial_setup)

    # *** start blockchain propagator manager in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_manager)

    # *** start blockchain propagator initiator in separate thread ***
    reactor.callInThread(blockchain_propagator.run_propagator_convo_initiator)

    # *** Instantiate Network Propagator ***
    propagator = NetworkPropagator(
        mempool=mempool,
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

    # *** instantiate network message sorter ***
    network_message_sorter = NetworkMessageSorter(
        q_object_from_protocol,
        q_for_bk_propagate,
        q_for_propagate,
        node=None,
        admin=admin,
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
        reg_network_sandbox=False
    )

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
        None,  # q object to each node is None
        is_program_running,  # Event object to set to true or false
        is_not_in_process_of_creating_new_block,  # Event object used to wait for best time to exit
        None,  # DummyInternet is None
        q_for_propagate,
        q_for_bk_propagate,
        q_for_compete,
        q_object_from_protocol,
        q_for_validator,
        q_for_block_validator,
        0  # number of nodes is zero because this is main function

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

    long_opts = ["live", "sandbox=", "mining=", "new"]  # if sandbox is put then number of nodes must be present
    # short_opts = "l s:n"

    try:
        optlist, args = getopt.getopt(sys.argv[1:], shortopts='', longopts=long_opts)
    except getopt.GetoptError as e:
        print(e)
    else:

        option_dict = dict(optlist)
        print(option_dict)

        if not option_dict:  # run default sandbox simulation
            sandbox_main(
                number_of_nodes=1,
                reg_network_sandbox=False,
                preferred_no_of_mining_nodes=0,
                just_launched=True
            )

        elif "--sandbox" in option_dict and "--live" not in option_dict:  # run sandbox mode

            no_of_nodes = int(option_dict["--sandbox"])
            mining_nodes = int(option_dict["--mining"]) if "--mining" in option_dict else 0

            # run sandbox with provided args
            sandbox_main(
                number_of_nodes=no_of_nodes,
                reg_network_sandbox=False,
                preferred_no_of_mining_nodes=mining_nodes,
                just_launched=True if "--new" in option_dict else False
            )

        elif "--sandbox" not in option_dict and "--live" in option_dict:  # run live mode
            main(
                just_launched=True if "--new" in option_dict else False
            )
        else:
            print(f" to run live node use: 'python start_node.py -l' OR\n"
                  f"'python start_node.py --live'\n")
            print(f"to run sandbox node use: 'python start_node.py --sandbox (no_nodes)' no_nodes should be how "
                  f"fake nodes to create.\nie 'python start_node.py --sandbox 2' will create 2 extra fake nodes\n"
                  f"you can also use 'python start_node.py -s (no_nodes)'  to create nodes")

    # sandbox_main(number_of_nodes=1, reg_network_sandbox=False, preferred_no_of_mining_nodes=0)


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








