from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Database_Core import RetrieveData, StoreData
import time


class AssignmentStatementValidator:
    """
    This class is instantiated by client and used to check validity of message,
    Then assign stmt send to node and this class is used by node to check also.
    if message is validated, node sends a ver message
    else a rej message is sent if invalid
    """
    def __init__(self, asgn_stmt_dict, wallet_pubkey=None, q_object=None):
        """

        :param asgn_stmt_dict: assignment statement dict with
        {
            asgn_stmt: ''
            sig: 'base85 encoded string which must be encoded into b'' byte string then base85 decoded'
            stmt_hsh: SHA256 hex hash of asgn_stmt
            client_id: id of wallet owner
        }

        asgn_stmt key: 'snd_wid|rcv_wid|bk_conn_wid|amt|fee|timestamp|timelimit'

        :param wallet_pubkey:
        :param q_object: a queue.Queue instance (or similar)
        """
        self.asgn_stmt_dict = asgn_stmt_dict
        self.asgn_stmt= asgn_stmt_dict["asgn_stmt"]
        self.asgn_stmt_list = asgn_stmt_dict["asgn_stmt"].split(sep='|')
        self.sending_wallet_pubkey = wallet_pubkey
        self.sending_wid = self.asgn_stmt_list[0]
        self.sending_client_id = asgn_stmt_dict["client_id"]
        self.signature = asgn_stmt_dict["sig"]
        self.stmt_hash = asgn_stmt_dict["stmt_hsh"]
        self.timestamp = self.asgn_stmt_list[-2]
        self.timelimit = self.asgn_stmt_list[-1]
        self.unknown_wallet = True if wallet_pubkey else False
        self.q_object = q_object

        self.set_sending_wallet_pubkey()

    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.sending_wallet_pubkey is None:
            snd_wid = self.asgn_stmt_list[0]

            self.sending_wallet_pubkey = RetrieveData.RetrieveData.get_pubkey_of_wallet(wid=snd_wid)
            # print(len(snd_wid))
            # print("sending pubkey: ", self.sending_wallet_pubkey)

    def check_validity(self):
        """
        checks validity, before checking validity, tries to retrieve pubkey of sending wallet.
        IF public key of sending wallet not found returns none.
        This causes ListenerMessage class to request for public key from sending wallet.
        When public key sent, it assumes wallet is an unknown wallet and stores public key for future reference

        Also Stores assignment statement details into a db for unfulfilled conditional statement
        'snd_wid|rcv_wid|bk_conn_wid|amt|fee|timestamp|timelimit'
        :return:
        """

        if self.sending_wallet_pubkey == "":
            return None
        elif (self.check_client_id_owner_of_wallet(),
                self.check_signature_valid(),
                self.check_timestamp(),
                self.check_inputs()
              ):
            if self.unknown_wallet:
                StoreData.StoreData.store_wallet_info_in_db(
                    wallet_id=self.sending_wid,
                    wallet_owner=self.sending_client_id,
                    wallet_pubkey=self.sending_wallet_pubkey
                )
            StoreData.StoreData.store_cond_asgn_stmt_info_in_db(
                amt=float(self.asgn_stmt_list[3]),
                fee=float(self.asgn_stmt_list[4]),
                snd_wid=self.asgn_stmt_list[0],
                rcv_wid=self.asgn_stmt_list[1],
                bk_conn_wid=self.asgn_stmt_list[2],
                sig=self.signature,
                time=self.timestamp,
                limit=self.timelimit,
                asgn_stmt=self.asgn_stmt,
                tx_hash=self.stmt_hash

            )

            # pass validated message to network propagator and competing process(if active)
            # 'a' reason message for assignment statement
            if self.q_object:
                self.q_object.put([f'a{self.stmt_hash[:8]}',  self.sending_wallet_pubkey.hex(), self.asgn_stmt_dict, True])
            return True
        else:
            if self.q_object:
                self.q_object.put([f'a{self.stmt_hash[:8]}',  self.sending_wallet_pubkey.hex(), self.asgn_stmt_dict, False])

            return False

    def check_client_id_owner_of_wallet(self):
        step1 = SHA256.new(self.sending_wallet_pubkey + self.sending_client_id.encode()).digest()
        derived_wid = "W" + RIPEMD160.new(step1).hexdigest()

        print("owner check: ", derived_wid == self.sending_wid)

        return derived_wid == self.sending_wid

    def check_signature_valid(self):
        response = DigitalSignerValidator.validate_wallet_signature(msg=self.asgn_stmt,
                                                                    wallet_pubkey=self.sending_wallet_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

    def check_timestamp(self):
        rsp = int(time.time()) < int(self.timestamp + self.timelimit)

        print("time check", rsp)
        return rsp

    def check_inputs(self):
        """
        checks inputs to make sure they of the proper data type ie amount is
        :return: True if inputs are of write data type else False
        """

        try:
            amt = float(self.asgn_stmt_list[3])
            fee = float(self.asgn_stmt_list[4])
        except ValueError:
            print("inputs Check: ", False)
            return False
        else:
            if amt > 0.0 and fee > 0.0: # verify amt and fee is not negative
                print("inputs Check: ", True)
                return True
            else:
                print("inputs Check: ", False)
                return False




