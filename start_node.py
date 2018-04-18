from Orses_Administrator_Core.Administrator import Admin
from Orses_Network_Core.NetworkManager import NetworkManager
from Orses_Network_Messages_Core.NetworkPropagator import NetworkPropagator


from getpass import getpass
from twisted.internet import reactor

import sys, multiprocessing, queue

p_version = sys.version_info

assert (p_version.major >= 3 and p_version.minor >= 6), "must be running python 3.6.0 or greater\n" \
                                                        "goto www.python.org to install/upgrade"

# todo: figure out how connection protocols can be saved, and messages coming from the connection is identified
# todo: so far when connection is made, the Instance sends itself using queue, then when messages are received
# todo: the instance sends itself as the key and msg as value.

# todo: goal is to be able to signal when a new conversation(not new connection) is started between nodes and ways to
# todo: signal new conversation and end existing conversation

"""
file used to start node
1 load or create admin class
2. if admin.isCompetitor is None ask to create new competitor msg. if false, skip. if true, ask if would like compete
    
3 start Network Propagator, used to propagate validated network messages

4. start Network Listener and Validator process
"""

# loads or, if not yet created, creates new admin details. Also Creates the necessary database for running node

admin_name = input("admin name: ")
password = getpass("password: ")

admin = Admin(admin_name=admin_name, password=password, newAdmin=False).load_user()
if admin is None:
    ans = input("No admin id under that admin name, would you like to create a new admin id? y/N ")
    if ans.lower() == "y":
        admin = Admin(admin_name=admin_name, password=password, newAdmin=True)


# Start competing process if admin.isCompetitor == True

if admin.isCompetitor is True:
    compete = input("Start Competing? Y/n(default is Y)")
    if compete.lower() in {"y", ""}:
        print("Competing Process Started...")
elif admin.isCompetitor is None:
    compete = input("Would You like to compete to create blocks on the Orses Network?\n"
                    "press enter to skip, y for yes or n for no: ").lower()

    if compete == "y":
        print("\n a new competitor message will be sent to the network and included in the blockchain. \n"
              "Once it has at least 10 confirmations. Blocks created by your node will be accepted by other competitors")
        admin.isCompetitor = True
        # todo: add logic to create new competitor network message for inclusion into the blockchain
    elif compete == "n":
        admin.isCompetitor = False
else:
    compete = 'n'


# instantiate queue variables
q_for_compete = multiprocessing.Queue() if compete == 'y' else None
q_for_validator = multiprocessing.Queue()
q_for_propagate = queue.Queue()


# start network propagator a different process using multiprocessing
propagator = NetworkPropagator(q_for_validator, q_for_propagate, q_for_compete)
network_propagator_process = multiprocessing.Process(target=propagator.run_propagator)
network_propagator_process.daemon = True
network_propagator_process.start()


# start network manaager and run veri node factory and regular factory using reactor.callFromThread
network_manager = NetworkManager(admin=admin, q_object_from_network_propagator=q_for_propagate)
reactor.callFromThread(network_manager.run_veri_node_network, reactor, q_for_propagate)
reactor.callFromThread(network_manager.run_regular_node_network, reactor, q_for_propagate)




