"""

This file will contain a class representing an instance of each proxy responsibility.

This means for each wallet this node is a proxy of, an instance of WalletProxy() will be used to manage the
responsibilities of the node to a wallet

Each walletProxy should have:

admin instance of main node
wallet id of Blockchain Connected Wallet
pubkey and private key unique

new_mode = If the proxy was just created then this is set to True but default is False

If WalletProxy represents a new proxy-bcw relationship then a new public/private key pair is created and public
key is returned. This public key is used by ProxyCenter to create a proxy acceptance msg, This message is stored under
the "WSH" section


"""

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Orses_Cryptography_Core.PKIGeneration import PKI
from Orses_Validator_Core.AssignmentStatementValidator import AssignmentStatementValidator
from Orses_Util_Core import  Filenames_VariableNames


class WalletProxy:
    def __init__(self, proxy_center, bcw_wid: str, new_proxy=False, overwrite=False):
        self.admin_inst = proxy_center.admin_inst
        self.db_manager = self.admin_inst.get_db_manager()
        self.bcw_wid = bcw_wid
        self.bcw_filename = f"proxy_{bcw_wid}"
        self.bcw_folder_name = self.admin_inst.fl.get_wallet_proxy_folder_path(
            proxy_name=Filenames_VariableNames.wallet_proxy_folder.format(self.bcw_wid)
        )
        self.bcw_proxy_pubkey = None
        self.bcw_proxy_privkey = None
        self.new_proxy = new_proxy
        self.overwrite = overwrite

        # lowest batch no is 1 (not 0)
        self.current_proxy_batch_no = None

        self.current_list_of_stmt_hash = list()

        # {batch_no: [wallet state hash,block_no_saved, amount of tokens volume, fee earned]}
        self.proxy_batch_with_wsh_dict = None

        self.__set_or_create_pki_pair()

    def __set_or_create_pki_pair(self):

        # create an instance of PKI class (uses RSA 3072)
        pki = PKI(username=self.bcw_filename, password=self.admin_inst.password, user_instance=self)

        if self.new_proxy is True:
            pki.generate_pub_priv_key(
                save_in_folder=self.bcw_folder_name,
                overwrite=self.overwrite
            )

        self.bcw_proxy_pubkey = pki.load_pub_key(
            importedKey=False,
            x_y_only=True,
            user_or_wallet='wallet',  # use wallet, given WalletProxy acts similar to a wallet
            in_folder=self.bcw_folder_name

        )
        self.bcw_proxy_privkey = pki.load_priv_key(in_folder=self.bcw_folder_name)

        if not self.bcw_proxy_privkey or not self.bcw_proxy_pubkey:
            print(f"In WalletProxy.py not able to load pubkey or privkey. might not exist") if self.new_proxy is False\
                else print(f"In WalletProxy.py not able to generate and load privkey or pubkey")
            return

        # create or load leveldb databases for administration
        # this includes db that stores all assignment statements sent to the administered BCW
        # a db that stores all wallets with their managed by BCW

        self.__create_load_necessary_files_folders_databases()

    def __create_load_necessary_files_folders_databases(self):
        """
        Will create or load
        :return:
        """

        batch_no = self.admin_inst.fl.open_file_from_json(
            filename="current_batch_file",
            in_folder=self.bcw_folder_name
        )

        batch_no_with_wsh_details = self.admin_inst.fl.open_file_from_json(
            filename='batch_details_file',
            in_folder=self.bcw_folder_name
        )

        if batch_no:
            self.current_proxy_batch_no = batch_no
        if batch_no_with_wsh_details:
            self.proxy_batch_with_wsh_dict = batch_no_with_wsh_details

    def execute_asgn_stmt_both_managed(self, asgn_stmt_dict, stmt_list, snd_balance, wallet_pubkey=None):


        # validate assignment statement
        validator = AssignmentStatementValidator(
            admin_instance=self.admin_inst,
            asgn_stmt_dict=asgn_stmt_dict,
            asgn_stmt_list=stmt_list,
            snd_balance=snd_balance,
            wallet_pubkey=wallet_pubkey
        ).check_validity()

        if validator is None:
            return None
        elif validator is False:
            return False

        # *** move funds ***

        # asgn_stmt_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]

        snd_wid = stmt_list[0]
        rcv_wid = stmt_list[1]
        amt = int(round(float(stmt_list[3]), 10) * 1e10)
        fee = int(round(float(stmt_list[4]), 10) * 1e10)

        # update snd balance
        snd_tmp_bal = self.db_manager.get_from_wallet_balances_db(wallet_id=snd_wid)
        snd_deduction = (amt + fee)
        snd_tmp_bal[0] = snd_tmp_bal[0] - snd_deduction
        snd_tmp_bal[2] = snd_tmp_bal[0] + snd_tmp_bal[1]
        self.db_manager.insert_into_wallet_balances_db(wallet_id=snd_wid)

        # update rcv balance
        rcv_tmp_bal = self.db_manager.get_from_wallet_balances_db(wallet_id=rcv_wid)
        rcv_tmp_bal[0] = rcv_tmp_bal[0] + amt
        rcv_tmp_bal[2] = rcv_tmp_bal[0] + rcv_tmp_bal[1]
        rcv_tmp_bal.insert(3, self.bcw_wid)  # specifically uses insert() to avoid Error if len == 3 (rather than 4)
        self.db_manager.insert_into_wallet_balances_db(wallet_id=rcv_wid)


        # create an notification message

        notif_msg = dict()

        notif_msg['type'] = "exec_asgn"
        notif_msg['msg_hash'] = asgn_stmt_dict["stmt_hsh"]
        notif_msg['proxy_sig'] = DigitalSigner.sign_with_provided_privkey(
            dict_of_privkey_numbers=self.bcw_proxy_privkey,
            message=asgn_stmt_dict["stmt_hsh"]

        )
        notif_msg["proxy_id"] = self.admin_inst.admin_id
        notif_msg["bcw_wid"] = self.bcw_wid
        notif_msg["amount"] = amt
        notif_msg["fee"] = fee
        notif_msg['snd'] = snd_wid
        notif_msg['rcv'] = rcv_wid
        notif_msg['sc4'] = True  # executed using scenario 4, which is both sender and receiver managed by proxy node

        return notif_msg


    def execute_asgn_stmt_snd_managed(self, asgn_stmt_dict, stmt_list, snd_balance, wallet_pubkey=None):
        pass

    def execute_asgn_stmt_rcv_managed(self, asgn_stmt_dict, stmt_list, snd_balance, wallet_pubkey=None):

        # validate assignment statement
        validator = AssignmentStatementValidator(
            admin_instance=self.admin_inst,
            asgn_stmt_dict=asgn_stmt_dict,
            asgn_stmt_list=stmt_list,
            snd_balance=snd_balance,
            wallet_pubkey=wallet_pubkey
        ).check_validity()

        if validator is None:
            return None
        elif validator is False:
            return False


    def execute_asgn_stmt_nonoe_managed(self, asgn_stmt_dict, stmt_list):
        pass


    def get_pubkey(self):

        if self.bcw_proxy_pubkey:
            return self.bcw_proxy_pubkey
        else:
            return {}

    def sign_a_message(self, msg: str):
        """
        used to sign a message
        :param msg:
        :return:
        """
