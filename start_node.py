from Orses_Administrator_Core.Administrator import Admin
from Orses_Network_Core.NetworkManager import NetworkManager
from Orses_Network_Messages_Core.NetworkPropagator import NetworkPropagator
from twisted.internet.error import CannotListenError

# https://superuser.com/questions/127863/manually-closing-a-port-from-commandline

from getpass import getpass
from twisted.internet import reactor

import sys, multiprocessing, queue

p_version = sys.version_info

assert (p_version.major >= 3 and p_version.minor >= 6), "must be running python 3.6.0 or greater\n" \
                                                        "goto www.python.org to install/upgrade"

# todo: start competing/block creation process, finish up the blockchain process
# todo: user can exit program by typing "exit" or "quit" and pressing enter.
# todo: Build a way to finish up any conversations with peers before ending program

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

    :param args: should be list of blocking objects: in this case q objects
    :return:
    """
    print(args)
    def temp():
        if reactor_instance.running:
            print("Node Started. To Stop Node Safely, type 'exit' or 'quit' without quote and press enter.")
            while True:
                ans = input("cmd: ").lower()

                if ans in {"exit", "quit"}:
                    for i in args:
                        print("this is i", i)
                        if isinstance(i, multiprocessing.queues.Queue):
                            print(i)
                            i.put(ans)

                    reactor_instance.stop()
                    print("reactor still running?: ", reactor_instance.running)
                    break
    reactor_instance.callInThread(temp, )

def main():
    admin_name = input("admin name: ")
    password = getpass("password: ")

    admin = Admin(admin_name=admin_name, password=password, newAdmin=False).load_user()
    if admin is None:
        ans = input("No admin id under that admin name, would you like to create a new admin id? y/N ")
        if ans.lower() == "y":
            admin = Admin(admin_name=admin_name, password=password, newAdmin=True)


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
                  "Once it has at least 10 confirmations. Blocks created by your node will be accepted by other competitors")
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


    # start compete process, if compete is yes
    if compete == 'y':
        pass

    # *** start network propagator a different process using multiprocessing ***
    propagator = NetworkPropagator(q_for_validator, q_for_propagate, reactor, q_for_compete)
    network_propagator_listener_process = reactor.callInThread(propagator.run_propagator_convo_manager)
    network_propagator_speaker_process = reactor.callInThread(propagator.run_propagator_convo_initiator)
    # network_propagator_process.daemon = True
    # network_propagator_process.start()


    # start network manaager and run veri node factory and regular factory using reactor.callFromThread
    network_manager = NetworkManager(admin=admin, q_object_from_network_propagator=q_for_propagate,
                                     q_object_to_validator=q_for_validator, propagator=propagator, reg_listening_port=55600)
    reactor.callFromThread(network_manager.run_veri_node_network, reactor)
    reactor.callFromThread(network_manager.run_regular_node_network, reactor)
    reactor.callWhenRunning(send_stop_to_reactor, reactor, q_for_propagate, q_for_compete, q_for_validator)

    reactor.run()
    print("Node Stopped")


if __name__ == '__main__':
    try:
        main()
    except (SystemExit, KeyboardInterrupt) as e:
        print(e)

# try:
#     reactor.run()
# except (SystemExit, KeyboardInterrupt):
#     print("program stopped")
#     reactor.stop()
# except CannotListenError:
#     print("can't listen")
#     reactor.stop()
# except Exception as e:
#     print(e)
#     reactor.stop()




