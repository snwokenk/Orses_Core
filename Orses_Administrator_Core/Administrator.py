from Orses_Cryptography_Core.PKIGeneration import PKI
from Orses_Database_Core.CreateDatabase import CreateDatabase
from Orses_Util_Core.Filenames_VariableNames import admins_folder


from Crypto.Hash import SHA256, RIPEMD160
import time, os, pathlib, json


class Admin:

    def __init__(self, admin_name, password, newAdmin=False):
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
        """
        self.admin_name = admin_name
        self.password = password
        self.admin_id = None
        self.creation_time = None
        self.pubkey = None
        self.privkey = None
        self.newAdmin = newAdmin
        self.isNewAdmin = newAdmin

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
            pki.generate_pub_priv_key(save_in_folder=admins_folder, overwrite=False)

            # load public key, loaded as bytes and not key object
            self.pubkey = pki.load_pub_key(importedKey=False)

            # load private key, loaded as key object ready to be used for signing or encrypting
            self.privkey = pki.load_priv_key()

            # set client ID
            self.admin_id = self.__create_admin_id()

            # if the a new admin then creation time is now and new databases are created with initial info stored

            self.creation_time = int(time.time())
            CreateDatabase().create_admin_db(self.admin_name)
            self.save_admin()

        elif self.isNewAdmin is False:
            pass

    def __create_admin_id(self):

        step1 = SHA256.new(self.pubkey).digest()
        return "ID-" + RIPEMD160.new(step1).hexdigest()