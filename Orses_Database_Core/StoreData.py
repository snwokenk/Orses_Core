from Orses_Database_Core.Database import Sqlite3Database
from Orses_Util_Core import Filenames_VariableNames

# TODO: create method for storing token reservation request

class StoreData:

    @staticmethod
    def store_admin_info_in_db(admin_id, pubkey, username, timestamp_of_creation, isCompetitor, user_instance):
        db = Sqlite3Database(dbName=Filenames_VariableNames.admin_dbname.format(username),
                             in_folder=user_instance.fl.get_admin_data_folder_path())

        db.insert_into_table(tableName=Filenames_VariableNames.admin_info_tname.format(username),
                             admin_id=admin_id, pubkey=pubkey, username=username,
                             timestamp_of_creation=timestamp_of_creation, isCompetitor=isCompetitor)

        db.close_connection()

    @staticmethod
    def store_wallet_info_in_db(wallet_id, wallet_owner, wallet_pubkey, user_instance):

        db = Sqlite3Database(dbName=Filenames_VariableNames.wallet_id_dbname,
                             in_folder=user_instance.fl.get_clients_wallet_folder_path())

        db.insert_into_table(tableName=Filenames_VariableNames.wallet_id_tname, wallet_id=wallet_id,
                             wallet_owner=wallet_owner, wallet_pubkey=wallet_pubkey)

        db.close_connection()

    @staticmethod
    def store_cond_asgn_stmt_info_in_db(tx_hash, snd_wid, rcv_wid, bk_conn_wid, time, limit, fee, amt, sig,
                                        asgn_stmt, user_instance):

        db = Sqlite3Database(dbName=Filenames_VariableNames.asgn_stmt_dbname,
                             in_folder=user_instance.fl.get_mempool_data_folder_path())

        db.insert_into_table(tableName=Filenames_VariableNames.asgn_stmt_tname, tx_hash=tx_hash, snd_wid=snd_wid,
                             rcv_wid=rcv_wid, bk_conn_wid=bk_conn_wid, time=time, Timelimit=limit, fee=fee, amt=amt,
                             sig_base85=sig, asgn_stmt=asgn_stmt)
        db.close_connection()

    @staticmethod
    def store_fulfilled_asgn_stmt_info_in_db():
        pass

    @staticmethod
    def store_token_transfer_tx_info_in_db(tx_hash, snd_wid, rcv_wid, time, fee, amt, sig, json_ttx_dict,
                                           user_instance):

        db = Sqlite3Database(dbName=Filenames_VariableNames.ttx_dbname,
                             in_folder=user_instance.fl.get_mempool_data_folder_path())

        db.insert_into_table(tableName=Filenames_VariableNames.ttx_tname,tx_hash=tx_hash, snd_wid=snd_wid,
                             rcv_wid=rcv_wid,  timestamp=time,  fee=fee, amt=amt,
                             sig_base85=sig, json_ttx_dict=json_ttx_dict)

        db.close_connection()

    @staticmethod
    def store_token_rsv_req_info_in_db(tx_hash, wid, amt, fee, timestamp, expiration, owner_id, sig, json_trr_dict,
                                       user_instance):
        """

        :param tx_hash: SHA 256 hash of request
        :type tx_hash: str
        :param wid: wallet id reserving tokens
        :type wid: str
        :param amt: amount of tokens reserved
        :type amt: float
        :param fee: amount of fees >= 1
        :type fee: float
        :param time1: timestamp of request
        :type time1: int
        :param expiration: expiration of reservation >= 2592000
        :type expiration: int
        :param owner_id: client id owning wallet
        :type owner_id: str
        :param sig: base85 encoded signature string
        :type sig: str
        :param json_tkr_dict: json encoded dictionary of all data
        :type json_tkr_dict: str
        :param user_instance: instance of admin or user object
        :return: None
        """
        db = Sqlite3Database(dbName=Filenames_VariableNames.trr_dbname,
                             in_folder=user_instance.fl.get_mempool_data_folder_path())

        db.insert_into_table(tableName=Filenames_VariableNames.trr_tname, tx_hash=tx_hash, wid=wid, amt=amt, fee=fee,
                             timestamp=timestamp, expiration=expiration, owner_id=owner_id, sig_base85=sig,
                             json_trr_dict=json_trr_dict)
        db.close_connection()

    @staticmethod
    def store_token_revoke_req_in_db(tx_hash, trr_hash, wid, fee, timestamp, owner_id, sig, json_trx_dict,
                                     user_instance):

        db = Sqlite3Database(dbName=Filenames_VariableNames.trx_dbname,
                             in_folder=user_instance.fl.get_mempool_data_folder_path())

        db.insert_into_table(tableName=Filenames_VariableNames.trx_tname, tx_hash=tx_hash, trr_hash=trr_hash,
                             wid=wid, fee=fee, timestamp=timestamp, owner_id=owner_id, sig_base85=sig,
                             json_trx_dict=json_trx_dict)
        db.close_connection()


if __name__ == '__main__':
    pass