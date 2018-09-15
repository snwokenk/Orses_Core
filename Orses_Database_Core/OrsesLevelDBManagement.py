import plyvel, os, json


class OrsesLevelDBManager:

    def __init__(self, admin_inst):
        self.admin_inst = admin_inst
        self.databases = dict()
        self.prefix_db = dict()

    def load_required_databases(self):
        req_db_list = [
            "wallet_balances",
            "wallet_pubkeys"
            "temp_wallet_balances"
            "unconfirmed_msgs_hashes"
            "unconfirmed_msgs_wid"

        ]

        for i in req_db_list:
            self.load_db(name=i, create_if_missing=True)

    def get_from_unconfirmed_db_wid(self, wallet_id: str, only_value=True):
        """

        :param wallet_id:
        :param only_value:
        :return: list of lists:
            [[tx_type, "sender" or "receiver, main_tx, sig, tx_hash, amt_tokens(sender=neg., receiver=pos. ], ....]
        """

        try:
            # wallet balance = [b'wallet id', b'[free token amount, reserved token amount]'
            wallet_activity = self.databases["unconfirmed_msgs_wid"].get(key=wallet_id.encode())
        except KeyError:
            # load up db
            self.load_db(name="unconfirmed_msgs_wid", create_if_missing=False)
            return self.get_from_unconfirmed_db_wid(wallet_id=wallet_id)
        except plyvel.Error:
            print(f"Error in OrsesLevelDBManager, wallet_balances DB does not exist")
            return False
        else:

            if wallet_activity and only_value:
                wallet_activity = json.loads(wallet_activity[1].decode())
            elif wallet_activity:
                wallet_activity = [wallet_activity[0].decode(), json.loads(wallet_activity[1].decode())]
            else:
                wallet_activity = []

            return wallet_activity

    def insert_into_unconfirmed_db_wid(self, tx_type: str, sending_wid: str, tx_hash: str, signature: str,
                                       main_tx: dict, amt: int, fee: int, rcv_wid=None):
        """
        Insert into db using wallet id as key
        :param sending_wid:
        :param tx_hash: hash
        :param signature: signature of transaction
        :param main_tx: dict containting the main details of a msg
        :param amt: amount involved tx is for, if it is a ttx or rvk_req or rsv_req then it should be > 0
        :param fee: amount to be paid to administrators/blockcreators. should always be (fee > 0)
        :return:
        """

        # get previous activities if any and add to it
        snd_prev_activity = self.get_from_unconfirmed_db_wid(wallet_id=sending_wid, only_value=True)
        rcv_prev_activity = self.get_from_unconfirmed_db_wid(wallet_id=sending_wid, only_value=True) if rcv_wid else \
            None

        if snd_prev_activity:
            # number to subtract is fees and amount
            snd_prev_activity.append([tx_type, 'sender', main_tx, signature, tx_hash, -fee, -amt])
            value = json.dumps(snd_prev_activity)
        else:

            # number to add is amt, fees are taken by block creator
            value = json.dumps([[tx_type, 'sender', main_tx, signature, tx_hash, amt]])

        if rcv_prev_activity:
            rcv_prev_activity.append([tx_type, 'receiver', main_tx, signature, tx_hash])
            value1 = json.dumps(rcv_prev_activity)
        else:
            value1 = None


        try:
            with self.databases["unconfirmed_msgs_wid"].write_batch(transaction=True) as wb:
                wb.put(key=sending_wid.encode(), value=value.encode())
                if value1:
                    wb.put(key=rcv_wid.encode(), value=value1.encode())

        except KeyError:
            # print(f"in OrsesLevelDBManagement: keyerror occured, Loading db called 'wallet_balances'")
            self.load_db(name="unconfirmed_msgs_wid")
            return self.insert_into_unconfirmed_db_wid(
                sending_wid=sending_wid,
                tx_hash=tx_hash,
                signature=signature,
                main_tx=main_tx,
                tx_type=tx_type,
                amt=amt,
                fee=fee
            )
        else:
            return True

    def insert_into_unconfirmed_db(self, tx_type: str, sending_wid: str, tx_hash: str, signature: str,
                                   main_tx: dict, amt: int, fee: int, rcv_wid=None):
        """
        This inserts hash of message
        :param sending_wid:
        :param tx_hash:
        :param signature:
        :param main_tx:
        :param rcv_wid: if tx_type is ttx or transfer transaction then rcv_wid should not be none
        :return:
        """

        value = json.dumps([main_tx, signature, rcv_wid, sending_wid])

        try:
            self.databases["unconfirmed_msgs_hashes"].put(key=tx_hash.encode(), value=value.encode())
        except KeyError:
            # print(f"in OrsesLevelDBManagement: keyerror occured, Loading db called 'wallet_balances'")
            self.load_db(name="unconfirmed_msgs_hashes")
            return self.insert_into_unconfirmed_db(
                sending_wid=sending_wid,
                tx_hash=tx_hash,
                signature=signature,
                main_tx=main_tx,
                tx_type=tx_type,
                rcv_wid=rcv_wid,
                amt=amt,
                fee=fee
            )
        else:
            is_inserted = self.insert_into_unconfirmed_db_wid(
                sending_wid=sending_wid,
                tx_hash=tx_hash,
                signature=signature,
                main_tx=main_tx,
                tx_type=tx_type,
                amt=amt,
                fee=fee
            )
        if is_inserted:
            return True
        else:
            return False

    def get_a_prefixed_db(self, db_name: str, prefix: str, create_if_not_exist=True):
        """
        this returns a prefixed_db class.
        a prefixed db class allows you to put a key/value pair with the prefixed value
        ie if your key was wallet id b"wf443434034" and value was b'[500, 0]'. The prefixed db class
        with a prefix of b'0-' would insert your key as b"0-wf443434034" when calling put.

        if you decide to get the wallet id, a prefixed db class would only check for
        the wallet id with a prefix of b"0-"

        :param db_name: the name of the leveldb database to create a prefixed db class from
        :param prefix: the prefix to use
        :param create_if_not_exist: create a prefix db if it does not exist (does not create a new leveldb
        if it does not exist)
        :return: the prefixed db class or
                if leveldb has not been loaded or prefixed db does not exist and create_if_not_exist == False
        """

        try:
            if prefix in self.prefix_db:
                tmp = self.prefix_db[prefix]
            elif create_if_not_exist:
                tmp = self.databases[db_name].prefixed_db(prefix.encode())
                self.prefix_db[prefix] = tmp
            else:
                print(f"in OrsesLevelDBManager: prefixed db: {prefix} does not exist and create_if_not_exist is False")
                return None
        except KeyError:
            print(f"Error, Troubleshoot, database {db_name} not loaded")
            return None

        else:
            return tmp


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

    def insert_into_wallet_balances_prefixed_db(self, wallet_id: str, wallet_data: list, prefix: str):
        """
        a leveldb database stores the wallet balances of all wallets managed by the blockchain
        :param wallet_id: wallet id to update
        :param wallet_data: json_encoded wallet data of balances:
                            [int, int, int] = [free token balance, reserved_token_balance, total token]
        :return: bool, true if successul
        """
        wallet_data = json.dumps(wallet_data)
        db_prefix = self.get_a_prefixed_db(db_name="temp_wallet_balances", prefix=prefix)
        if not db_prefix:
            return False
        else:
            db_prefix.put(key=wallet_id.encode(), value=wallet_data.encode())
            return True

    def get_from_temp_wallet_balances_prefixed_db(self, wallet_id: str, prefix: str, only_value=True):
        """
        use to retrieve wallet balance data
        :param wallet_id:
        :return: if only_value is True then [free token balance, reserved_token_balance, total token] else
                [wallet id, [free token balance, reserved_token_balance, total token]]
        """

        db_prefix = self.get_a_prefixed_db(db_name="temp_wallet_balances", prefix=prefix, create_if_not_exist=False)
        if not db_prefix:
            return False
        else:
            wallet_balance = db_prefix.get(key=wallet_id.encode())
            if wallet_balance:
                wallet_balance = [wallet_balance.decode(), json.loads(wallet_balance[1].decode())]
            else:
                wallet_balance = [None, None, None]  # prefixed_balance should return None if no entry

            if wallet_balance and only_value:
                wallet_balance = wallet_balance[1]

            return wallet_balance


    def insert_into_wallet_balances_db(self, wallet_id: str, wallet_data: list):
        """
        a leveldb database stores the wallet balances of all wallets managed by the blockchain
        :param wallet_id: wallet id to update
        :param wallet_data: json_encoded wallet data of balances:
                            [int, int, int] = [free token balance, reserved_token_balance, total token]
        :return: bool, true if successul
        """
        # amounts are stored as ints of ntakiris ie 1 orses token = 10,000,000,000 (10 billion) ntakiris
        # amounts are sent over the network as floats with with max decimal places of 10
        # this means the minimum amount of orses token is  0.0000000001 or 01e-10 == 1 ntakiri
        wallet_data = json.dumps(wallet_data)
        try:
            self.databases["wallet_balances"].put(key=wallet_id.encode(), value=wallet_data.encode())
        except KeyError:
            # print(f"in OrsesLevelDBManagement: keyerror occured, Loading db called 'wallet_balances'")
            self.load_db(name="wallet_balances")
            return self.insert_into_wallet_balances_db(wallet_id=wallet_id, wallet_data=wallet_data)
        else:
            return True

    def get_from_wallet_balances_db(self, wallet_id: str, only_value=True):
        """
        use to retrieve wallet balance data
        :param wallet_id:
        :return: if only_value is True then [free token balance, reserved_token_balance, total token] else
                [wallet id, [free token balance, reserved_token_balance, total token]]
        """

        try:
            # wallet balance = [b'wallet id', b'[free token amount, reserved token amount]'
            wallet_balance = self.databases["wallet_balances"].get(key=wallet_id.encode())

        except KeyError:
            # load up db
            self.load_db(name="wallet_balances", create_if_missing=False)
            return self.get_from_wallet_balances_db(wallet_id=wallet_id)
        except plyvel.Error:
            print(f"Error in OrsesLevelDBManager, wallet_balances DB does not exist")
            return False
        else:
            if wallet_balance:
                wallet_balance = [wallet_balance.decode(), json.loads(wallet_balance[1].decode())]
            else:
                wallet_balance = [0,0,0]  # available, reserved, total

            if wallet_balance and only_value:
                wallet_balance = wallet_balance[1]

            return wallet_balance


if __name__ == '__main__':
    try:
        db = plyvel.DB("Sam1", create_if_missing=True)
    except plyvel.Error as e:
        print(e)
    else:


        db_0_pref = db.prefixed_db(b"0-")

        db_0_pref.put(b"sam", b"Is great")
        db.put(b'sam', b"is handsome")

        for i in db:
            print(i)


        db.close()
