import plyvel, os


class OrsesLevelDBManager:

    def __init__(self, admin_inst):
        self.admin_inst = admin_inst
        self.databases = dict()

    def load_required_databases(self):
        req_db_list = [
            "wallet_balances",
            "wallet_pubkeys"
        ]

        for i in req_db_list:
            self.load_db(name=i, create_if_missing=True)

    def load_db(self, name: str, create_if_missing=True):
        """
        loads
        :param name:
        :return:
        """
        filename = os.path.join(self.admin_inst.fl.get_clients_wallet_folder_path(), name)
        try:
            db = plyvel.DB(filename, create_if_missing=create_if_missing)
        except plyvel.Error as e:
            print(f"in CreateALevelDB, error occured: {e}")
        else:
            self.databases[name] = db

    def insert_into_wallet_balances_db(self, wallet_id: str, wallet_data: str):
        """
        a leveldb database stores the wallet balances of all wallets managed by the blockchain
        :param wallet_id: wallet id to update
        :param wallet_data: json_encoded wallet data of balances
        :return:
        """
        try:
            self.databases["wallet_balances"].put(key=wallet_id.encode(), value=wallet_data.encode())
        except KeyError:
            # print(f"in OrsesLevelDBManagement: keyerror occured, Loading db called 'wallet_balances'")
            self.load_db(name="wallet_balances")
            return self.insert_into_wallet_balances_db(wallet_id=wallet_id, wallet_data=wallet_data)
        else:
            return True

    def get_from_wallet_balances_db(self, wallet_id: str):
        """
        use to retrieve wallet balance data
        :param wallet_id:
        :return:
        """

        try:
            self.databases["wallet_balances"].get(key=wallet_id)
        except KeyError:
            # load up db
            self.load_db(name="wallet_balances", create_if_missing=False)
            return self.get_from_wallet_balances_db(wallet_id=wallet_id)
        except plyvel.Error:
            print(f"Error in OrsesLevelDBManager, wallet_balances DB does not exist")
            return False
        else:
            return True


if __name__ == '__main__':
    try:
        db = plyvel.DB("Sam1", create_if_missing=True)
    except plyvel.Error as e:
        print(e)

    print(db.closed)

    db.close()

    print(db.closed)