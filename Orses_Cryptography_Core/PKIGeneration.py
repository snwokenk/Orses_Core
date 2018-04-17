"""
generates Public Private Key Pairs for use in generating Client ID
RSA-3072 used

"""

from Crypto.PublicKey import RSA
from Orses_Cryptography_Core.Encryption import Encrypt
from Orses_Util_Core.FileAction import FileAction
from Orses_Util_Core import Filenames_VariableNames
from Orses_Cryptography_Core.Decryption import Decrypt


class PKI:
    def __init__(self, username, password):
        self.combinedkey = RSA.generate(3072)
        self.username = username
        self.password = password
        self.pubkey = None
        self.privkey_file = Filenames_VariableNames.priv_key_filename.format(username)
        self.pubkey_file = Filenames_VariableNames.pub_key_filename.format(username)

    def generate_pub_priv_key(self, save_in_folder=None, overwrite=False):

        if overwrite is False and self.load_pub_key():
            return "Keys under that username and client id already exist"


        # set pubkey
        self.pubkey = self.combinedkey.publickey().exportKey()

        # encrypting private key
        encrypted_key_list = Encrypt(self.combinedkey.exportKey(format="PEM", pkcs=8), password=self.password).encrypt()

        # save keys are saved using user name
        self.__save_key(encrypted_key_list, save_in_folder=save_in_folder)

        # returning list of [ciphertext, tag, nonce, salt]
        return encrypted_key_list

    def __save_key(self, encrypted_key_list, save_in_folder):

        # save public key in file named username_pubkey
        FileAction.save_json_into_file(self.pubkey_file, python_json_serializable_object=self.pubkey.hex(),
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
                filename=self.privkey_file, in_folder=Filenames_VariableNames.admins_folder)
        else:
            list_of_encrypted_privkey_tag_nonce_salt = FileAction.open_file_from_json(
                filename=self.privkey_file, in_folder=Filenames_VariableNames.wallets_folder)

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
            return RSA.importKey(decrypted_key)
        else:
            return decrypted_key

    def load_pub_key(self, importedKey=True, user_or_wallet="user"):

        if user_or_wallet == "user":
            pubkey_hex = FileAction.open_file_from_json(
                self.pubkey_file, in_folder=Filenames_VariableNames.admins_folder)
        else:
           pubkey_hex =  FileAction.open_file_from_json(
               self.pubkey_file, in_folder=Filenames_VariableNames.wallets_folder)

        if not pubkey_hex:
            return False
        pubkey_bytes = bytes.fromhex(pubkey_hex)

        if importedKey is True:
            return RSA.importKey(pubkey_bytes)
        else:
            return pubkey_bytes


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
    publicKey = PKI(username="snwokenk", password="7433xxxxxx")

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