from Orses_Database_Core.Database import Sqlite3Database
from Orses_Util_Core import Filenames_VariableNames

"""
inputs and outputs
CreateDatabase file and class is used to create the pertinent files needed to administrate the network. 
Databased to create are:
for blockchain support:

- Wallet Info Database, (only wallet that has received tokens before):
    wallet id, wallet_owner, wallet pubkey, wallet_owner pubkey,
     
- conditional Assignment Statement Database, create for each day, previous day consolidated with fullfiled(valid):
    tx_hash, bk_connected_wid, snd_wid, rcv_wid, amt, fee, time, limit(in seconds), asgn_stmt, signature

- fulfilled Assignment Statement Database, :
    fulfilled_asgn_stmt_dict(json format), snd, rcv, bk_con_wid, time_fulfilled,

- transfer transaction (only valid):
    snd wid, rcv wid, amt, fee, time, tx_hash, sig, wallet_owner id
    
- token reservation request:
    req _wid, amt, fee, time, exp, proxies, rsv_req, signature, tx_hash
    

"""


class CreateDatabase:

    def __init__(self):
        self._create_client_id_info_db()
        self._create_wallet_id_info_db()
        self._create_cond_asgn_stmt_db()
        self._create_fulfilled_asgn_stmt_db()
        self._create_tkn_rsv_req_db()
        self._create_transfer_tx_db()
        # self._create_blockchain_db()
        self._create_tkn_rvk_req_db()

    @staticmethod
    def create_admin_db(username):
        """
        creates a database named username_admin_data
        password is hashed, can be used to provide password check (even though EAX already does)
        :param username: string,
        :param password: string,
        :return: None
        """

        db = Sqlite3Database(dbName=Filenames_VariableNames.admin_dbname.format(username),
                             in_folder=Filenames_VariableNames.admin_data)

        db.create_table_if_not_exist(tableName=Filenames_VariableNames.admin_info_tname.format(username),
                                     A_admin_id="TEXT", B_pubkey="TEXT", C_username="TEXT",
                                     D_timestamp_of_creation="INT", E_isCompetitor="BLOB")
        db.close_connection()

    @staticmethod
    def _create_client_id_info_db():
        db = Sqlite3Database(dbName=Filenames_VariableNames.client_id_dbname,
                             in_folder=Filenames_VariableNames.clients_wallets_data)
        db.create_table_if_not_exist(tableName=Filenames_VariableNames.client_id_tname, primary_key="client_id",
                                     A_client_id="TEXT", B_client_pubkey="TEXT")

        db.close_connection()


    @staticmethod
    def _create_wallet_id_info_db():

        db = Sqlite3Database(
            dbName=Filenames_VariableNames.wallet_id_dbname,
            in_folder=Filenames_VariableNames.clients_wallets_data
        )

        db.create_table_if_not_exist(
            tableName=Filenames_VariableNames.wallet_id_tname, primary_key="wallet_id",
            A_wallet_id="TEXT", B_wallet_owner="TEXT", C_wallet_pubkey="BLOB"
        )

        db.close_connection()

    @staticmethod
    def _create_cond_asgn_stmt_db():
        """
        tx_hash, bk_connected_wid, snd_wid, rcv_wid, amt, fee, time, limit(in seconds), asgn_stmt, signature
        :return: None
        """

        db = Sqlite3Database(dbName=Filenames_VariableNames.asgn_stmt_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)

        db.create_table_if_not_exist(tableName=Filenames_VariableNames.asgn_stmt_tname, primary_key="tx_hash",
                                     A_tx_hash="TEXT", B_bk_conn_wid="TEXT", C_snd_wid="TEXT",
                                     D_rcv_wid="TEXT", E_amt="REAL", F_fee="REAL", G_time="INT", H_Timelimit="INT",
                                     I_asgn_stmt="TEXT", J_sig_base85="TEXT")

        db.close_connection()


    @staticmethod
    def _create_fulfilled_asgn_stmt_db():
        """
        tx_hash, snd, rcv, bk_con_wid, time_fulfilled, sig, fulfilled_asgn_stmt_dict(json)
        :return:
        """

        db = Sqlite3Database(dbName=Filenames_VariableNames.fulfilled_asgn_stmt_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)

        db.create_table_if_not_exist(tableName=Filenames_VariableNames.fulfilled_asgn_stmt_tname, primary_key="tx_hash",
                                     A_tx_hash="TEXT", B_snd_wid="TEXT", C_rcv_wid="TEXT", D_bk_con_wid="TEXT",
                                     E_time_fulfilled="INT", F_sig_base85="TEXT", G_json_fulfil_dict="TEXT")
        db.close_connection()

    @staticmethod
    def _create_transfer_tx_db():
        db = Sqlite3Database(dbName=Filenames_VariableNames.ttx_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)

        db.create_table_if_not_exist(tableName=Filenames_VariableNames.ttx_tname, primary_key="tx_hash",
                                     A_tx_hash="TEXT", B_snd_wid="TEXT", C_rcv_wid="TEXT", D_amt="REAL", E_fee="REAL",
                                     F_timestamp="INT", G_sig_base85="TEXT", H_json_ttx_dict="TEXT")

        db.close_connection()

    @staticmethod
    def _create_tkn_rsv_req_db():
        db = Sqlite3Database(dbName=Filenames_VariableNames.trr_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)

        db.create_table_if_not_exist(tableName=Filenames_VariableNames.trr_tname, primary_key="tx_hash",
                                     A_tx_hash="TEXT", B_wid="TEXT", C_amt="REAL", E_fee="REAL", F_timestamp="INT",
                                     G_expiration="INT", H_owner_id="TEXT", I_sig_base85="TEXT", J_json_trr_dict="TEXT")

        db.close_connection()

    @staticmethod
    def _create_tkn_rvk_req_db():
        db = Sqlite3Database(dbName=Filenames_VariableNames.trx_dbname,
                             in_folder=Filenames_VariableNames.mempool_data)

        db.create_table_if_not_exist(tableName=Filenames_VariableNames.trx_tname, primary_key="tx_hash",
                                     A_tx_hash="TEXT", B_trr_hash="TEXT", C_wid="TEXT", D_fee="REAL", E_timestamp="INT",
                                     F_owner_id="TEXT", G_sig_base85="TEXT", H_json_trx_dict="TEXT")

        db.close_connection()

    @staticmethod
    def _create_blockchain_db():
        db = Sqlite3Database(dbName=Filenames_VariableNames.blockchain_dbname,
                             in_folder=Filenames_VariableNames.block_folder)
        db.close_connection()

    @staticmethod
    def _create_block_table():
        # create table representing block
        pass
