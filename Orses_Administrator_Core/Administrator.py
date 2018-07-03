from Orses_Cryptography_Core.PKIGeneration import PKI
from Orses_Database_Core.CreateDatabase import CreateDatabase
from Orses_Util_Core.FileAction import FileAction
from Orses_Database_Core.StoreData import StoreData
from Orses_Database_Core.RetrieveData import RetrieveData
from Orses_Util_Core.FileAction import FileAction
from Orses_Util_Core import Filenames_VariableNames


from Crypto.Hash import SHA256, RIPEMD160
import time, os, pathlib, json


# TODO; make sure created database is same as database name to store and retrieve data

class Admin:

    def __init__(self, admin_name, password, newAdmin=False, isCompetitor=None, is_sandbox=False):
        """
        class representing the admin.
        This class should allow for an admin to:

        -Validate transactions
        -Propagate validated transactions to other admin/verification node
        -Become A Proxy Node for a blockchain connected wallet
        -Compete to become a blockcreator
        -store validated transactions in appropriate database/table
        -store the Genesis block and Orses blockchain(all or a part depending()
        -store transaction states and details of
        -receive balance query from wallet client nodes and be able to respond with blockchain-based balance
            and blockchain+mempool balance


        :param admin_name: string, keys and admin details are stored under admin_name
        :param password: password used to encrypt private keys and/or details
        :param newAdmin: bool, true if new admin, false if not
        :param isCompetitor: None, True, False, none if never set, True if admin_id identified as competitor on
            blockchain, False if specifically set by user (will not be prompted to set)
        """
        self.admin_name = admin_name
        self.password = password
        self.admin_id = None
        self.creation_time = None
        self.pubkey = None
        self.privkey = None
        self.pki = None
        self.fl = FileAction(username=admin_name)
        self.newAdmin = newAdmin
        self.isNewAdmin = newAdmin
        self.isCompetitor = isCompetitor
        self.is_sandbox = is_sandbox

        self.__set_or_create_pki_pair()

    def __set_or_create_pki_pair(self):
        """
        sets or, if not already created, creates public private key pair for admin_name on local machine.
        :return: none
        """

        # create an instance of PKI class (uses RSA 3072)
        pki = PKI(username=self.admin_name, password=self.password)

        # try to load pub key, it should return false if new admin, if it returns pubkey then admin with admin_name already created
        rsp = pki.load_pub_key()

        if rsp and self.newAdmin is True:
            self.isNewAdmin = False
            return

        # overwrites admin_name
        elif self.newAdmin is True:
            pki.generate_pub_priv_key(save_in_folder=self.fl.get_keys_folder_path(), overwrite=False)

            # set self.pki to pki
            self.pki = pki

            # load public key, loaded as bytes and not key object
            self.pubkey = pki.load_pub_key(importedKey=False)

            # load private key, loaded as key object ready to be used for signing or encrypting
            self.privkey = pki.load_priv_key()

            # set client ID
            self.admin_id = self.__create_admin_id()

            # if the a new admin then creation time is now and new databases are created with initial info stored


            self.creation_time = int(time.time())

            # create all the databases needed in either sandbox/username or live_data/username folders
            CreateDatabase(user_instance=self)
            self.save_admin()

        elif self.isNewAdmin is False:
            pass

    def __create_admin_id(self):

        step1 = SHA256.new(self.pubkey).digest()
        return "VID-" + RIPEMD160.new(step1).hexdigest()

    def save_admin(self):
        # todo: STOPPED HERE direct from segregated folder
        # pubkey should be saved as a json encoded python dictonary
        StoreData.store_admin_info_in_db(
            admin_id=self.admin_id,
            pubkey=json.dumps(self.pki.load_pub_key(x_y_only=True)),
            username=self.admin_name,
            timestamp_of_creation=self.creation_time,
            isCompetitor=self.isCompetitor,
            user_instance=self
        )

    def load_user(self):
        admin_data = RetrieveData.get_admin_info(username=self.admin_name, user_instance=self)

        pki = PKI(username=self.admin_name, password=self.password)
        if admin_data:
            self.admin_id = admin_data[0]
            self.creation_time = admin_data[1]
            self.isCompetitor = admin_data[2]
            self.pubkey = pki.load_pub_key(importedKey=False)
            self.privkey = pki.load_priv_key(importedKey=True)
            self.pki = pki

            print("in Administrator.py/load_user(), self.pubkey: ", self.pubkey)

        else:  # no user info, user not created
            return None

        if self.privkey:  # everything is well
            # creates user info database and wallet info database (if not already created)
            CreateDatabase()
            return self
        else: # wrong password
            return False

    def export_user(self):
        """
        used to export user into a file, which can then be taken anywhere else
        :return:
        """

        # pki = PKI(username=self.admin_name, password=self.password)
        exp_path = os.path.join(pathlib.Path.home(), "Desktop", "Orses_External_Files", "Exported_Accounts",
                                self.admin_name + ".orses")

        FileAction.create_folder("Exported_Accounts")

        user_info_dict = dict()
        user_info_dict["admin_name"] = self.admin_name
        user_info_dict["admin_id"] = self.admin_id
        user_info_dict["creation_time"] = self.creation_time
        user_info_dict["pubkey_dict"] = self.pki.load_pub_key(x_y_only=True)
        user_info_dict["encrypted_private_key"] = self.pki.load_priv_key(importedKey=False, encrypted=True)

        with open(exp_path, "w") as outfile:
            json.dump(user_info_dict, outfile)

        return True

    def import_user(self, different_admin_name=None):
        """
        used to import using username and password

        first checks to make sure no user by the same

        -if no file found with username on Imported_Accounts folder  returns none

        -if username found but password is wrong, returns False

        -if user found and everything okay returns self (or instance of user class)
        :return: None, False or self (instance of user).
        """

        imp_path = os.path.join(pathlib.Path.home(), "Desktop", "Orses_External_Files", "Imported_Accounts",
                                self.admin_name + ".orses")



        try:
            with open(imp_path, "r") as infile:
                admin_data = json.load(infile)
        except FileNotFoundError:
            return None

        # instantiate a pki class
        pki = PKI(username=self.admin_name, password=self.password)

        # get privkey name for user to see if any file exist
        priv_filename = Filenames_VariableNames.priv_key_filename.format(self.admin_name)
        rsp = FileAction.open_file_from_json(filename=priv_filename, in_folder=Filenames_VariableNames.admin_data)

        if rsp:
            if different_admin_name is None:
                # this will raise an exception if user already exists
                raise Exception("Admin With admin_name '{}' Already Exists".format(self.admin_name))

        # if different username is specified, then user will be saved under that name
        if different_admin_name:
            self.admin_name = different_admin_name
            priv_filename = Filenames_VariableNames.priv_key_filename.format(self.admin_name)
            pki = PKI(username=self.admin_name, password=self.password)

        # save and load privkey
        FileAction.save_json_into_file(priv_filename,
                                       python_json_serializable_object=admin_data["encrypted_private_key"],
                                       in_folder=Filenames_VariableNames.admin_data)

        self.privkey = pki.load_priv_key(importedKey=True)

        # if priv key is false
        if not self.privkey:
            FileAction.delete_file(filename=priv_filename, in_folder=Filenames_VariableNames.admin_data)
            return False

        # save pubkey hex to file and set pubkey, pubkey saved in hex format, self.pubkey is set to bytes format
        pub_filename = Filenames_VariableNames.pub_key_filename.format(self.admin_name)
        FileAction.save_json_into_file(pub_filename, python_json_serializable_object=admin_data["pubkey_dict"],
                                       in_folder=Filenames_VariableNames.admin_data)
        self.pubkey = pki.load_pub_key(importedKey=False)


        # set admin id
        self.admin_id = admin_data["admin_id"]

        # set creation time
        self.creation_time = admin_data["creation_time"]



        # create database and save (will also create general client id and wallet id info database)
        CreateDatabase().create_admin_db(self.admin_name)
        self.save_admin()

        return self