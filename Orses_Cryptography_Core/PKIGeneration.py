"""
generates Public Private Key Pairs for use in generating Client ID
RSA-3072 used

"""

from Crypto.PublicKey import ECC
from Orses_Cryptography_Core.Encryption import Encrypt
from Orses_Util_Core.FileAction import FileAction
from Orses_Util_Core import Filenames_VariableNames
from Orses_Cryptography_Core.Decryption import Decrypt
import base64


class PKI:
    def __init__(self, username, password, user_instance=None):
        self.combinedkey = ECC.generate(curve="P-256")
        self.username = username
        self.password = password
        self.user_instance = user_instance
        self.pubkey = None
        self.privkey_file = Filenames_VariableNames.priv_key_filename.format(username)
        self.pubkey_file = Filenames_VariableNames.pub_key_filename.format(username)

    def generate_pub_priv_key(self, save_in_folder=None, overwrite=False):

        if overwrite is False and self.load_pub_key():
            return "Keys under that username and client id already exist"

        x_coord = int(self.combinedkey.pointQ.x).to_bytes(length=32, byteorder="big")
        y_coord = int(self.combinedkey.pointQ.y).to_bytes(length=32, byteorder="big")

        # set pubkey of ECC and save x and y numbers
        self.pubkey = {
            "x": base64.b85encode(x_coord).decode(),
            "y": base64.b85encode(y_coord).decode()
        }

        # encrypting private key
        d_coord = int(self.combinedkey.d).to_bytes(length=32, byteorder="big")
        encrypted_key_list = Encrypt(plaintext=base64.b85encode(d_coord).decode(), password=self.password).encrypt()

        # save keys are saved using user name
        self.__save_key(encrypted_key_list, save_in_folder=save_in_folder)

        # returning list of [ciphertext, tag, nonce, salt]
        return encrypted_key_list

    def __save_key(self, encrypted_key_list, save_in_folder):

        # save public key in file named username_pubkey
        FileAction.save_json_into_file(self.pubkey_file, python_json_serializable_object=self.pubkey,
                                       in_folder=save_in_folder)

        # save private key in file named username_encrypted_key
        FileAction.save_json_into_file(self.privkey_file, python_json_serializable_object=encrypted_key_list,
                                       in_folder=save_in_folder)

    def load_priv_key(self, importedKey=True, encrypted=False, user_or_wallet="user"):
        """
        1. loads json object of [privkey_encrypted, tag, nonce, salt]
        2. Turns these from hex to bytes
        3. using these information and the provided password, it decrypts private key a

        :return: bytes
        """

        # load encryped private key list with tag, nonce and salt
        if user_or_wallet == "user":
            list_of_encrypted_privkey_tag_nonce_salt = FileAction.open_file_from_json(
                filename=self.privkey_file, in_folder=self.user_instance.fl.get_keys_folder_path())
        else:
            list_of_encrypted_privkey_tag_nonce_salt = FileAction.open_file_from_json(
                filename=self.privkey_file, in_folder=self.user_instance.fl.get_wallets_folder_path)

        # if it is an empty list then no key created and saved on username so generate new key
        if not list_of_encrypted_privkey_tag_nonce_salt:
            return b''

        if encrypted:
            return list_of_encrypted_privkey_tag_nonce_salt

        # turn elements from hex back to bytes
        list_of_encrypted_privkey_tag_nonce_salt = [bytes.fromhex(i) for i in list_of_encrypted_privkey_tag_nonce_salt]

        # decrypt encrypted key
        decrypted_key = Decrypt(list_of_encrypted_privkey_tag_nonce_salt, password=self.password).decrypt()

        if importedKey is True and decrypted_key:
            pubkey = self.load_pub_key(x_y_only=True, user_or_wallet=user_or_wallet)
            x_int = base64.b85decode(pubkey["x"].encode())
            x_int = int.from_bytes(x_int, "big")

            y_int = base64.b85decode(pubkey["y"].encode())
            y_int = int.from_bytes(y_int, "big")

            d_int = base64.b85decode(decrypted_key)
            d_int = int.from_bytes(d_int, "big")

            return ECC.construct(d=d_int, point_x=x_int, point_y=y_int, curve="P-256")
        else:
            return decrypted_key

    def load_pub_key(self, importedKey=True, x_y_only=False, user_or_wallet="user"):

        if user_or_wallet == "user":
            pubkey = self.user_instance.fl.open_file_from_json(
                self.pubkey_file, in_folder=self.user_instance.fl.get_keys_folder_path())
        else:
           pubkey = self.user_instance.fl.open_file_from_json(
               self.pubkey_file, in_folder=self.user_instance.fl.get_wallets_folder_path())

        if not pubkey:  # no public key saved with user name
            return False

        if importedKey is True and x_y_only is False:

            # construct public key and return a key object or importedKey
            x_int = base64.b85decode(pubkey["x"].encode())
            x_int = int.from_bytes(x_int, "big")

            y_int = base64.b85decode(pubkey["y"].encode())
            y_int = int.from_bytes(y_int, "big")
            return ECC.construct(point_x=x_int, point_y=y_int, curve="P-256")
        elif x_y_only is True:
            # returns a dictionary with {"x": base85 string, "y": base85 string}
            # this string can be turned back into number using:
            # x_int = base64.b85decode(string.encode())
            # x_int = int.from_bytes(x_int, "big")
            return pubkey
        else:
            # turn back to original bytes from base85encoded string/bytes
            pubkey_bytes = base64.b85decode(pubkey['x'].encode())+base64.b85decode(pubkey['y'].encode())

            # looking for bytes probably to generate user id
            # bytes is done by concatenating the bytes of x and y. see explanation above on how to get the bytes

            return pubkey_bytes

    @staticmethod
    def generate_key_from_parts(x: str, y: str, d=None, in_bytes=False):
        """
        used to generate key from x and y sent over the internet
        :param x: x + y used for pubkey generation
        :param y:
        :param d: x+y+d used for private key genereation
        :return: pubkey object
        """
        if in_bytes:
            # if in bytes then only for pubkey
            return base64.b85decode(x.encode())+base64.b85decode(y.encode())

        # if d is none returns pubkey
        return ECC.construct(curve="P-256", point_x=x, point_y=y, d=d)

    @staticmethod
    def convert_dict_keys_to_int(dict_with_x_y_d: dict):

        new_key_dict = dict()
        try:
            for key_attr in dict_with_x_y_d:
                new_key_dict[key_attr] = int.from_bytes(base64.b85decode(dict_with_x_y_d[key_attr].encode()), "big")
        except AttributeError:  # key_attr must be a str
            return None

        else:
            return new_key_dict

    @staticmethod
    def convert_dict_keys_to_str(self, dict_with_x_y_d: dict):

        new_key_dict = dict()
        try:
            for key_attr in dict_with_x_y_d:
                new_key_dict[key_attr] = int(key_attr).to_bytes(length=32, byteorder="big")
        except AttributeError:  # key_attr must be an int
            return None

        else:
            return new_key_dict




class WalletPKI(PKI):

    def __init__(self, wallet_nickname, password):
        """
        used to generate pki specifically for wallets
        keys are saved under wallet nickname. privkey is saved in a list [encrypted key, tag, nonce, salt]
        each element is a hex format and must be turned to bytes for use
        :param wallet_nickname:
        :param password:
        """
        super().__init__(username=wallet_nickname, password=password)
        self.privkey_file = Filenames_VariableNames.wallet_priv_key_filename.format(wallet_nickname)
        self.pubkey_file = Filenames_VariableNames.wallet_pub_key_filename.format(wallet_nickname)

    def __save_key(self, encrypted_key_list, save_in_folder):

        FileAction.save_json_into_file(self.pubkey_file,
                                       python_json_serializable_object=self.pubkey.hex(),
                                       in_folder=save_in_folder)
        FileAction.save_json_into_file(self.privkey_file,
                                       python_json_serializable_object=encrypted_key_list,
                                       in_folder=save_in_folder)


if __name__ == '__main__':
    publicKey = PKI(username="snwokenk", password="xxxxxx")

    print(publicKey.generate_pub_priv_key())
    # key = RSA.generate(3072)
    #
    # priv = key.exportKey(format="PEM", pkcs=8)
    #
    # privhex = priv.hex()
    # print(privhex)
    #
    # priv1 = bytes.fromhex(privhex)
    # print(priv1 == priv)