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

A Blockchain Connected Wallet has 2 other sections on it's balance "payables" and "receivables"


"""

from twisted.internet import threads

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Orses_Cryptography_Core.PKIGeneration import PKI
from Orses_Validator_Core.AssignmentStatementValidator import AssignmentStatementValidator
from Orses_Util_Core import  Filenames_VariableNames
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Proxy_Core.BCWTokenTransfer import BCWTokenTransfer


class WalletProxy:
    def __init__(self, proxy_center, bcw_wid: str, new_proxy=False, overwrite=False):
        self.proxy_center = proxy_center
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

        print(f"in WalletProxy __set_or_create_pki_pair, bcw_filename {self.bcw_filename}\n"
              f"bcw folder name {self.bcw_folder_name}")
        # create an instance of PKI class (uses ECDSA)
        pki = PKI(username=self.bcw_filename, password=self.admin_inst.password, user_instance=self.admin_inst)

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

        return self.update_balance(
            stmt_list=stmt_list,
            asgn_stmt_dict=asgn_stmt_dict,
            scenario_type='sc4'
        )


    def execute_asgn_stmt_snd_managed(self, asgn_stmt_dict, stmt_list, snd_balance, wallet_pubkey=None):
        pass

    def execute_asgn_stmt_rcv_managed(self, asgn_stmt_dict, stmt_list, snd_balance, snd_pending_tx,
                                      snd_bcw_manager: str, wallet_pubkey=None):
        """

        :param asgn_stmt_dict: full assignment statement dict sent by sender
        :param stmt_list: string of main assignment statment turned to list
        :param snd_balance: balance of sender's wallet
        :param snd_pending_tx:
        :param snd_bcw_manager: bcw managing sender's wallet, if none then sender's wallet directly on blockchain
        :param wallet_pubkey:
        :return:
        """

        snd_wid = stmt_list[0]
        rcv_wid = stmt_list[1]
        amt = int(round(float(stmt_list[3]), 10) * 1e10)
        fee = int(round(float(stmt_list[4]), 10) * 1e10)

        # Get the balance of sender's wallet, factoring any unconfirmed txs
        if snd_pending_tx:
            snd_balance = WalletInfo.get_lesser_of_wallet_balance(
                admin_inst=self.admin_inst,
                wallet_id=snd_wid
            )

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


        # create BCW initiated token transfer if directly on blockchain else

        if snd_bcw_manager is None:
            # create BCW initiated Token Transfer
            tmp_dict = BCWTokenTransfer(
                wallet_proxy=self,
                asgn_stmt_dict=asgn_stmt_dict
            ).sign_and_return_bcw_initiated_token_transfer(bcw_proxy_privkey=self.bcw_proxy_privkey)
        # create a balance transfer request if managed by
        elif isinstance(snd_bcw_manager, str):

            # if not managed by
            tmp_dict = {}


        def a_callable():
            return self.update_balance(stmt_list=stmt_list, asgn_stmt_dict=asgn_stmt_dict, scenario_type='sc2')

        return ['defer', tmp_dict, a_callable]

    def execute_asgn_stmt_none_managed(self, asgn_stmt_dict, stmt_list):
        pass

    def get_pubkey(self):

        if self.bcw_proxy_pubkey:
            return self.bcw_proxy_pubkey
        else:
            return {}

    def sign_a_message(self, msg: str, enc="base85"):
        """
        used to sign a message
        :param msg:
        :param enc: type of encoding, currently using 'base85' but 'base64' will soon be available
        :return:
        """

        sig = DigitalSigner.sign_with_provided_privkey(
            dict_of_privkey_numbers=self.bcw_proxy_privkey,
            message=msg
        )

        if sig:
            return sig
        else:
            return ''

    def update_balance(self, stmt_list, asgn_stmt_dict, scenario_type):
        """

        :param stmt_list:
        :param asgn_stmt_dict:
        :param scenario_type: sc4, sc3, sc2, sc1
        :return:
        """
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
        self.db_manager.insert_into_wallet_balances_db(wallet_id=snd_wid, wallet_data=snd_tmp_bal)

        # update rcv balance
        rcv_tmp_bal = self.db_manager.get_from_wallet_balances_db(wallet_id=rcv_wid)
        rcv_tmp_bal[0] = rcv_tmp_bal[0] + amt
        rcv_tmp_bal[2] = rcv_tmp_bal[0] + rcv_tmp_bal[1]
        rcv_tmp_bal.insert(3, self.bcw_wid)  # specifically uses insert() to avoid Error if len == 3 (rather than 4)
        self.db_manager.insert_into_wallet_balances_db(wallet_id=rcv_wid, wallet_data=rcv_tmp_bal)

        # create an notification message
        notif_msg = dict()

        notif_msg['type'] = "exec_asgn"
        notif_msg['msg_hash'] = asgn_stmt_dict["stmt_hsh"]
        notif_msg['proxy_sig'] = DigitalSigner.sign_with_provided_privkey(
            dict_of_privkey_numbers=None,
            message=asgn_stmt_dict["stmt_hsh"],
            key=self.bcw_proxy_privkey

        )
        notif_msg["proxy_id"] = self.admin_inst.admin_id
        notif_msg["bcw_wid"] = self.bcw_wid
        notif_msg["amount"] = amt
        notif_msg["fee"] = fee
        notif_msg['snd'] = snd_wid
        notif_msg['rcv'] = rcv_wid
        notif_msg[scenario_type] = True  # executed using scenario 4, which is both sender and receiver managed by proxy node

        return notif_msg