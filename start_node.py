from Orses_Administrator_Core.Administrator import Admin
from Orses_Network_Core.NetworkManager import NetworkManager
from Orses_Network_Messages_Core.NetworkPropagator import NetworkPropagator
from Orses_Network_Messages_Core.BlockchainPropagator import BlockChainPropagator
from Orses_Network_Core.NetworkMessageSorter import NetworkMessageSorter
from twisted.internet.error import CannotListenError

# for sandbox internet

from Orses_Dummy_Network_Core.DummyNetworkObjects import *

# https://superuser.com/questions/127863/manually-closing-a-port-from-commandline

from getpass import getpass
from twisted.internet import reactor, defer, threads

import sys, multiprocessing, queue, getopt, time

p_version = sys.version_info

assert (p_version.major >= 3 and p_version.minor >= 6), "must be running python 3.6.0 or greater\n" \
                                                        "goto www.python.org to install/upgrade"


# todo: finish export/import admin copy from Orses_Client since that has been done

# todo: in send_token() and reserve_token() in Orses.py add a way of updating tokens and activities

# todo: create a test genesis block, block 1 and block 2. in block add some wallets that can be used

# todo: try to create a mock twisted protocol class, This class will receive message using a pipe, this
# todo: will be for testing internal testing of network propagation and validation.
# todo: This class then be used in a Start_virtual_node script which will allow for testing of certian functionaility

# todo: CONTINUE IMPLEMENTING ECC, MAKE SURE LOAD PUBKEY AND PRIVKEY ARE IMPLEMENTING ECC AND NOT RSA

# todo: refactor convo_dict in blockchainpropagator and self.convo_id

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
def send_stop_to_reactor(reactor_instance, *args):
    """
    runs once the reactor is running, opens another thread that runs local function temp().
    This function waits for an exit signal, it then sends exit signal to other threads running, using the queue objects
    THese exit signals then trigger for other break off any loops and exit program

    :param args: should be list of blocking objects: in this case q objects
    :return:
    """
    print(args)

    def temp():

        if reactor_instance.running:
            print("\nNode Started. To Stop Node Safely, type 'exit' or 'quit' without quote and press enter.\n")
            while True:
                ans = input("cmd: ").lower()

                if ans in {"exit", "quit"}:
                    for i in args:
                        if isinstance(i, (multiprocessing.queues.Queue, queue.Queue)):
                            i.put(ans)


                    break
            return ans


    # ******  THIS LINE IS IMPORTANT FOR CLEAN ENDING OF REACTOR ****** #
    # ****** THIS WAITS FOR EXIT SIGNAL AND THE FIRES CALLBACK WHICH RUNS reactor.stop() in the main thread ***** #
    response_thread = threads.deferToThread(temp)  # deffering blocking function to thread
    response_thread.addCallback(lambda x: reactor.stop())  # lambda function is fired when blocking function returns (and return anything)


def create_admins(number_of_admins_to_create: int):
    assert number_of_admins_to_create > 0, "number of admins to create must be at least 1"
    admins_list = list()
    while number_of_admins_to_create:
        admins_list.append(Admin(
            admin_name=f'v{number_of_admins_to_create}', password="xxxxxx", newAdmin=True, is_sandbox=True))
        number_of_admins_to_create -= 1

    return admins_list





def sandbox_main():
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

    # *** instantiate queue variables ***
    q_for_compete = multiprocessing.Queue() if compete == 'y' else None
    q_for_validator = multiprocessing.Queue()
    q_for_propagate = multiprocessing.Queue()
    q_for_bk_propagate = multiprocessing.Queue()
    q_for_block_validator = multiprocessing.Queue()  # between block validators and block propagators
    q_for_initial_setup = multiprocessing.Queue()  # goes to initial setup
    q_object_from_protocol = multiprocessing.Queue()  # goes from protocol to message sorter

    # start compete(mining) process, if compete is yes. process is started using separate process (not just thread)
    if compete == 'y':
        pass

    # *** start dummy internet

    dummy_internet = DummyInternet()

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
        q_for_validator,
        q_for_propagate,
        reactor,
        q_for_initial_setup,
        q_for_compete
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
        propagator=propagator,
        reg_listening_port=55600
    )

    # *** instantiate network message sorter ***
    network_message_sorter = NetworkMessageSorter(q_object_from_protocol, q_for_bk_propagate, q_for_propagate)

    # *** run sorter in another thread ***
    reactor.callInThread(network_message_sorter.run_sorter)


    # *** use to connect to or listen for connection from other verification nodes ***
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
        q_for_propagate,
        q_for_bk_propagate,
        q_for_compete,
        q_object_from_protocol,
        q_for_validator,
        q_for_block_validator
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

    create_admins(2)
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








