from Orses_Administrator_Core.Administrator import Admin
from getpass import getpass
from twisted.internet import reactor
import sys

p_version = sys.version_info

assert (p_version.major >= 3 and p_version.minor >= 6), "must be running python 3.6.0 or greater\n" \
                                                        "goto www.python.org to install/upgrade"


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


# start network propagator process




