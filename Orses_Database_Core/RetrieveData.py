from Orses_Database_Core.Database import Sqlite3Database
from Orses_Util_Core import Filenames_VariableNames
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
    def get_pubkey_of_wallet(wid):
        """
        returns pubkey of wallet id
        :param wid: wallet id
        :return: base85 encoded wallet pubkey or empty string
        """
        print(wid_check(wid))

        if wid_check(wid=wid):

            db = Sqlite3Database(dbName=Filenames_VariableNames.wallet_id_dbname,
                                 in_folder=Filenames_VariableNames.data_folder)

            columnToSelect = "wallet_pubkey"
            boolCriteria = "wallet_id = '{}'".format(wid)

            pubkey = db.select_data_from_table(tableName=Filenames_VariableNames.wallet_id_tname,
                                               columnsToSelect=columnToSelect, boolCriteria=boolCriteria)

            print("pubkey return: ", pubkey)

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
                             in_folder=Filenames_VariableNames.data_folder)
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
                             in_folder=Filenames_VariableNames.data_folder)
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
                             in_folder=Filenames_VariableNames.data_folder)
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




