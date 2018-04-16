from CryptoHub_Wallet import Wallet
from CryptoHub_Util import Filenames_VariableNames, FileAction
from CryptoHub_Cryptography.PKIGeneration import WalletPKI
from CryptoHub_Message import AssignmentStatement, TransferTransaction, TokenReservationRequest, TokenReservationRevoke

# TODO: in associated_wallets create a w


class WalletServices:
    def __init__(self, client_id, user):
        self.user = user
        self.username = user.username
        self.password = user.password
        self.wallet_instance = None
        self.client_id = client_id
        self.associated_wallets = None
        self.__get_associated_wallets()

    def __get_associated_wallets(self):
        """
        used to get dictionary of wallet id's associated with Username.
        key is a nickname for each wallet, value is the wallet id
        if no wallet id, returns an empty dictionary
        :return: dict
        """

        filename = Filenames_VariableNames.username_wallets.format(self.username)
        folder_name = Filenames_VariableNames.wallet_details_folder
        username_wallets = FileAction.FileAction.open_file_from_json(filename=filename,
                                                                     in_folder=folder_name)
        if username_wallets:
            self.associated_wallets = username_wallets
        else:
            self.associated_wallets = {}

    def get_associated_wallet_ids(self):
        return self.associated_wallets

    def update_associated_wallet_id_dict(self, wallet_nickname, wallet_id):
        self.associated_wallets[wallet_nickname] = wallet_id
        filename = Filenames_VariableNames.username_wallets.format(self.username)
        folder_name = Filenames_VariableNames.wallet_details_folder
        FileAction.FileAction.save_json_into_file(filename=filename,
                                                  python_json_serializable_object=self.associated_wallets,
                                                  in_folder=folder_name)

    def create_wallet(self, wallet_nickname, balance, client_id, locked_token, password):

        wl = WalletPKI(wallet_nickname=wallet_nickname, password=password)
        wl.generate_pub_priv_key(save_in_folder=Filenames_VariableNames.wallets_folder)

        self.wallet_instance = Wallet.Wallet(balance=balance, client_id=client_id, locked_token=locked_token,
                                             pubkey=wl.load_pub_key(importedKey=False, user_or_wallet="wallet"),
                                             wallet_nickname=wallet_nickname)

        self.update_associated_wallet_id_dict(wallet_nickname=wallet_nickname,
                                              wallet_id=self.wallet_instance.get_wallet_id())

        self.wallet_instance.save_wallet_details(password=password)

        self.associated_wallets[wallet_nickname] = self.wallet_instance.get_wallet_id()
        return True

    def load_a_wallet(self, wallet_nickname, password):

        if wallet_nickname in self.associated_wallets:
            wallet_id = self.associated_wallets[wallet_nickname]
            self.wallet_instance = Wallet.Wallet.load_wallet_details(wallet_id=wallet_id, password=password,
                                                                     wallet_nickname=wallet_nickname)
            return True if self.wallet_instance else False
        else:
            return None

    def unload_wallet(self, save=False, password=None):
        if save:
            assert password is not None, "'password' parameter must not be None if 'save' parameter is True"
            if isinstance(self.wallet_instance, Wallet.Wallet):
                self.wallet_instance.save_wallet_details(password=password)

        self.wallet_instance = None

    def update_save_wallet_details(self, password):

        self.wallet_instance.save_wallet_details(password=password, username=self.username)

    def return_wallet_details(self):

        if isinstance(self.wallet_instance, Wallet.Wallet):
            return self.wallet_instance.get_wallet_details()
        else:
            return {}

    def get_privkey_of_wallet(self, password, imported_key=True):

        if isinstance(self.wallet_instance, Wallet.Wallet):
            return WalletPKI(wallet_nickname=self.wallet_instance.get_wallet_nickname(),
                             password=password).load_priv_key(importedKey=imported_key, user_or_wallet="wallet")
        else:
            return b''

    def validate_balances(self):
        pass

    def assign_tokens(self, receiving_wid, bk_connected_wid, amount_of_tokens, fee, password_for_wallet):
        asgn_stmt_object = AssignmentStatement.AssignmentStatement(
            sending_wid=self.wallet_instance.get_wallet_id(),
            receiving_wid=receiving_wid,
            bk_connected_wid=bk_connected_wid,
            amount_of_tokens=amount_of_tokens,
            fee=fee
        )

        assignment_statement = asgn_stmt_object.sign_and_return_conditional_assignment_statement(
            wallet_privkey=self.get_privkey_of_wallet(password=password_for_wallet)
        )

        if assignment_statement:

            # assignment_statement["wallet_id"] = self.wallet_instance.get_wallet_id()
            assignment_statement["client_id"] = self.client_id

            return assignment_statement
        else:
            return {}

    def transfer_tokens(self, receiving_wid, amount, fee, password_for_wallet):
        transfer_tx_obj = TransferTransaction.TokenTransferTransaction(
            sending_wid=self.wallet_instance.get_wallet_id(),
            receiving_wid=receiving_wid,
            amount_of_tokens=amount,
            fee=fee

        )

        transfer_transaction = transfer_tx_obj.sign_and_return_transfer_transaction(
            wallet_privkey=self.get_privkey_of_wallet(password=password_for_wallet)
        )

        if transfer_transaction:

            transfer_transaction["client_id"] = self.client_id

            return transfer_transaction

        else:  # returns empty dictionary because wallet privkey was not decrypted with right password
            return {}

    def become_bk_connected_wallet(self, amount, fee, wallet_password, time_limit, veri_node_proxies):
        tkn_req_obj = TokenReservationRequest.TokenReservationRequest(
            requesting_wid=self.wallet_instance.get_wallet_id(),
            time_limit=time_limit,
            tokens_to_reserve=amount,
            fee=fee

        )
        token_reservation_request = tkn_req_obj.sign_and_return_reservation_request(
            wallet_privkey=self.get_privkey_of_wallet(password=wallet_password),
            veri_node_proxies=veri_node_proxies
            # veri_node_proxies=["ID-fe1234abcd", "ID-ab1d3F457"]
        )

        if token_reservation_request:
            token_reservation_request["client_id"] = self.client_id

            return token_reservation_request

        else:
            return {}

    def verify_balance_on_blockchain(self, wallet_id):
        pass

