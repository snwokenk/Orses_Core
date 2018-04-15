from Crypto.Hash import SHA256, RIPEMD160
import json

from CryptoHub_Util import FileAction
from CryptoHub_Cryptography.Encryption import EncryptWallet
from CryptoHub_Cryptography.Decryption import WalletDecrypt
from CryptoHub_Util import Filenames_VariableNames
from CryptoHub_Database.UpdateData import UpdateData


import time

class Wallet:
    def __init__(self, wallet_nickname, pubkey, client_id, balance, locked_token, last_hash_state=None,
                 wallet_activities=None):
        """

        :param wallet_nickname:
        :param pubkey: bytes, not imported or in hex, when loading must convert back to bytes using bytes.fromhex()
        :param client_id:
        :param balance:
        :param locked_token:
        :param dict_of_activities: dictionary of dicits with keys being hash and list being
                keys {time, type(asgn _stmt or ttx), amount, sender, receiver, bk_conn_wallet}
        :param last_hash_state:  with SHA256 Hex String, if being loaded the include
        """
        self.wallet_nickname = wallet_nickname
        self.timestamp_of_creation = int(time.time())
        self.balance = balance
        self.locked_token_balance = locked_token
        self.wallet_id = None
        self.wallet_pub_key = pubkey
        self.client_id_of_owner = client_id
        self.activities = dict() if not isinstance(wallet_activities, dict) else wallet_activities
        self.last_saved_hash_state = last_hash_state
        self.__set_wallet_id(pubkey=pubkey)

    def __set_wallet_id(self, pubkey):
        """
        set wallet id using public key of wallet
        :param pubkey:
        :return:
        """

        step1 = SHA256.new(pubkey + self.client_id_of_owner.encode()).digest()
        self.wallet_id = "W" + RIPEMD160.new(step1).hexdigest()

    def get_wallet_nickname(self):
        """
        gets the nickname of wallet
        :return: string, self.nickname
        """
        return self.wallet_nickname

    def get_timestamp_of_creation(self):
        """
        gets the time wallet was created UTC
        :return: int, self.timestamp_of_creation
        """

        return self.timestamp_of_creation

    def get_balance(self):
        """
        gets amount of tokens associated with wallet id
        :return: float, self.balance
        """
        return self.balance

    def get_locked_token_balance(self):
        """
        gets amount of locked token associated with account
        :return: float, self.locked_token_balance
        """
        return self.locked_token_balance

    def get_wallet_id(self):
        """
        returns the wallet id
        :return: string, hexadecimal self.wallet_id
        """
        return self.wallet_id

    def get_wallet_pub_key(self):
        """
        returns the hex representation of pub key
        :return: string, hexadecimal self.wallet_pub_key
        """
        return self.wallet_pub_key

    def get_client_id_of_owner(self):
        return self.client_id_of_owner

    def get_last_saved_hash_state(self):
        return self.last_saved_hash_state

    def get_activities(self):
        return self.activities

    def add_to_balance(self, amount):

        # add more checks
        if isinstance(self.balance, (float, int)) and isinstance(amount, (float, int)):
            prev = self.balance
            self.balance += amount
            return [prev, self.balance, True]
        else:
            return [self.balance, self.balance, False]

    def add_to_locked_balance(self, amount):

        # add more checks
        if isinstance(self.locked_token_balance, (float, int)) and isinstance(amount, (float, int)) and amount > 0.00:
            prev = self.locked_token_balance
            self.locked_token_balance += amount
            return [prev, self.locked_token_balance, True]
        else:
            return [self.locked_token_balance, self.locked_token_balance, False]

    def subtract_from_balance(self, amount):
        """
        :param amount: non-negative float number
        :return:
        """
        # add more checks

        if isinstance(self.balance, (float, int)) and isinstance(amount, (float, int)) and amount > 0.00:
            prev = self.balance
            self.balance -= amount
            return [prev, self.balance, True]
        else:
            return [self.balance, self.balance, False]

    def subtract_from_locked_balance(self, amount):
        """
        :param amount: non-negative float number
        :return:
        """
        # add more checks

        if isinstance(self.locked_token_balance, (float, int)) and isinstance(amount, (float, int)) and amount > 0.00:
            prev = self.locked_token_balance
            self.locked_token_balance -= amount
            return [prev, self.locked_token_balance, True]
        else:
            return [self.locked_token_balance, self.locked_token_balance, False]

    def sub_balance_add_locked(self, amount, fee):

        rsp = self.subtract_from_balance(amount=amount+fee)
        rsp1 = self.add_to_locked_balance(amount=amount+fee)

        if rsp[-1] is True and rsp1[-1] is True:
            return True
        else:
            return False

    def update_to_activites(self, tx_obj, activity_type, act_hash):
        """

        This is used in AssignmentStatementValidator or TransferTransactionValidator
        If the assignment statements are validated, then it updates the wallet's activities variable
        hash {time, type(asgn _stmt or ttx), amount, sender, receiver, bk_conn_wallet}

        if assignment statement:
        [sending_wid, receiving_wid, bk_connected_wid, amount_of_tokens, fee, timestamp, timelimit]

        :param asgn_ttx, trr : assignment statement, transfer transaction or token reservation request
        :param activity_type: declares type, wheter asgn stmt or transfer transaction
        :return: bool
        """
        if activity_type == "asgn_stmt" and isinstance(tx_obj, list):
            d = dict()
            d["type"] = activity_type
            d["time"] = tx_obj[5]
            d["amount"] = tx_obj[3]
            d['fee'] = tx_obj[4]
            d["sender"] = tx_obj[0]
            d["receiver"] = tx_obj[1]
            d["bk_conn_wallet"] = tx_obj[2]

            self.activities.update({act_hash: d})
        elif activity_type == "ttx" and isinstance(tx_obj, dict):

            d = dict()
            d["type"] = activity_type
            d["time"] = tx_obj["time"]
            d["amount"] = tx_obj["amt"]
            d["fee"] = tx_obj["fee"]
            d["sender"] = tx_obj["snd_wid"]
            d["receiver"] = tx_obj["rcv_wid"]

            self.activities.update({act_hash: d})

        elif activity_type == "trr" and isinstance(tx_obj, dict):
            d = dict()
            d["type"] = activity_type
            d["time"] = tx_obj["time"]
            d["expiration"] = tx_obj["exp"]
            d["amount"] = tx_obj["amt"]
            d["fee"] = tx_obj["fee"]
            d["wid"] = tx_obj["req_wid"]
            d["vnode_proxies"] = tx_obj["v_node_proxies"]

            self.activities.update({act_hash: d})



    def get_wallet_details(self):

        wallet_details = {"details": {
            "wallet_nickname": self.wallet_nickname,
            "balance": self.balance,
            "locked_token_balance": self.locked_token_balance,
            "wallet_id": self.wallet_id,
            "wallet_pubkey": self.wallet_pub_key.hex(),
            "wallet_owner": self.client_id_of_owner,
            "timestamp_of_creation": self.timestamp_of_creation,
            "activities": self.activities
        }}

        self.last_saved_hash_state = SHA256.new(json.dumps(wallet_details["details"]).encode()).hexdigest()
        wallet_details["last_hash_state"] = self.last_saved_hash_state

        return wallet_details

    def save_wallet_details(self, password, username=None):

        encrypted_details = EncryptWallet(wallet_instance=self, password=password).encrypt()

        FileAction.FileAction.save_json_into_file(filename=self.wallet_id,
                                                  python_json_serializable_object=encrypted_details,
                                                  in_folder=Filenames_VariableNames.wallet_details_folder)

        if username:
            UpdateData.update_wallet_info_in_db(
                wallet_balance=self.balance,
                wallet_locked_balance=self.locked_token_balance,
                wallet_id=self.wallet_id,
                username=username

            )
        return True

    @staticmethod
    def load_wallet_details(wallet_id, wallet_nickname, password):
        wallet_details = FileAction.FileAction.open_file_into_json(filename=wallet_id,
                                                                   in_folder=Filenames_VariableNames.wallet_details_folder)
        wallet_details = [bytes.fromhex(i) for i in wallet_details]
        wallet_details = WalletDecrypt(ciphertext_tag_nonce_salt=wallet_details, password=password).decrypt()
        if not wallet_details:
            print("here")
            return False

        wallet_details = json.loads(wallet_details.decode())

        details = wallet_details["details"]
        last_hash_state = wallet_details["last_hash_state"]

        wallet = Wallet(pubkey=bytes.fromhex(details["wallet_pubkey"]), balance=details["balance"],
                        client_id=details["wallet_owner"], locked_token=details["locked_token_balance"],
                        wallet_nickname=wallet_nickname, last_hash_state=last_hash_state,
                        wallet_activities=details["activities"])

        return wallet
