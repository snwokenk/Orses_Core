from Orses_Database_Core.Database import Sqlite3Database
from Orses_Util_Core import Filenames_VariableNames
from Orses_Util_Core.FileAction import FileAction
from sqlite3 import OperationalError
import json


def wid_check(wid):
    try:
        bytes.fromhex(wid[1:])
    except ValueError:
        return False
    else:
        return True if (len(wid) == 41 and wid[0] == "W") else False


class RetrieveData:

    @staticmethod
    def get_admin_info(username, user_instance):
        db = Sqlite3Database(dbName=Filenames_VariableNames.admin_dbname.format(username),
                             in_folder=Filenames_VariableNames.admin_data)
        columnToSelect = "admin_id, timestamp_of_creation, isCompetitor"
        try:

            response = db.select_data_from_table(tableName=Filenames_VariableNames.admin_info_tname.format(username),
                                                 columnsToSelect=columnToSelect)
        except OperationalError:
            response = None
            db.delete_database()



        # returns [client_id, pubkey in hex format, timestamp_of_creation
        if response:
            db.close_connection()
            return response[0]
        return None

    @staticmethod
    def get_pubkey_of_wallet(wid):
        """
        returns pubkey of wallet id
        :param wid: wallet id
        :return: base85 encoded wallet pubkey or empty string
        """
        print(wid_check(wid))

        if wid_check(wid=wid):

            db = Sqlite3Database(dbName=Filenames_VariableNames.wallet_id_dbname,
                                 in_folder=Filenames_VariableNames.clients_wallets_data)

            columnToSelect = "wallet_pubkey"
            boolCriteria = "wallet_id = '{}'".format(wid)

            pubkey = db.select_data_from_table(tableName=Filenames_VariableNames.wallet_id_tname,
                                               columnsToSelect=columnToSelect, boolCriteria=boolCriteria)

            # print("(RetrieveData.py) pubkey return: ", pubkey)

            db.close_connection()

            if pubkey:
                return pubkey[0][0]

        return ""

    @staticmethod
    def get_hash_state_of_connected_wallets():
        pass

    @staticmethod
    def get_valid_transfer_transactions(tx_hash=None):
        """
        returns a dictionary in which:
        {'tx_hash': ['base_85 sig string', dictionary with keys: 'snd_wid', 'rcv_wid', 'timestamp', 'fee', 'amt']}
        :return:
        """
        db = Sqlite3Database(dbName=Filenames_VariableNames.ttx_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)
        columnToSelect = ['tx_hash', 'json_ttx_dict', 'sig_base85']
        boolCriteria = "tx_hash = '{}'".format(tx_hash) if tx_hash else None
        ttx = db.select_data_from_table(
            tableName=Filenames_VariableNames.ttx_tname,
            columnsToSelect=columnToSelect,
            boolCriteria=boolCriteria
        )
        db.close_connection()

        return {i[0]: [i[2], json.loads(i[1])] for i in ttx}

    @staticmethod
    def get_valid_competitors():
        pass

    @staticmethod
    def get_token_reservation_requests(tx_hash=None):
        """

        returns a dictionary in which:
        {'tx_hash': ['base_85 sig string', dictionary with keys: 'snd_wid', 'rcv_wid', 'timestamp', 'fee', 'amt']}
        :return: dict
        """
        db = Sqlite3Database(dbName=Filenames_VariableNames.trr_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)
        columnToSelect = ['tx_hash', 'json_trr_dict', 'sig_base85']
        boolCriteria = "tx_hash = '{}'".format(tx_hash) if tx_hash else None
        trr = db.select_data_from_table(
            tableName=Filenames_VariableNames.trr_tname,
            columnsToSelect=columnToSelect,
            boolCriteria=boolCriteria
        )

        return {i[0]: [i[2], json.loads(i[1])] for i in trr}

    @staticmethod
    def get_token_reservation_revoke_requests(tx_hash=None):
        """
        used to get all valid token reservation revoke requests
        :return:
        """

        db = Sqlite3Database(dbName=Filenames_VariableNames.trx_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)
        columnToSelect = ['tx_hash', 'json_trx_dict', 'sig_base85']
        boolCriteria = "tx_hash = '{}'".format(tx_hash) if tx_hash else None

        trx = db.select_data_from_table(
            tableName=Filenames_VariableNames.trx_tname,
            columnsToSelect=columnToSelect,
            boolCriteria=boolCriteria
        )

        return {i[0]: [i[2], json.loads(i[1])] for i in trx}




    @staticmethod
    def get_previous_block():
        """
        used to get info of previous block
        :return:
        """
        pass




