"""
contains class for decryption using AES256 and password key derivation

"""

from Crypto.Cipher import AES
from Crypto.Random import random
from getpass import getpass


# import from created modules
from Orses_Cryptography_Core.PasswordKeyGeneration import PasswordKey


class Decrypt:
    def __init__(self, ciphertext_tag_nonce_salt, password):
        """

        :param ciphertext_tag_nonce_salt: list of byte strings representing [ciphertext, tag, nonce, salt]
        :param username: username which keys were stored
        :param password: password used in pbkdf for key derivation
        """
        self.password = password
        self.salt = ciphertext_tag_nonce_salt[3]
        self.key_object = PasswordKey(password=self.password, salt=self.salt)
        self.ciphertext = ciphertext_tag_nonce_salt[0]
        self.tag = ciphertext_tag_nonce_salt[1]
        self.cipher = AES.new(key=self.key_object.get_key(), mode=AES.MODE_EAX, nonce=ciphertext_tag_nonce_salt[2])

    def decrypt(self):
        """
        decrypts ciphertext and returns unencrypted text (plaintext)
        :return: byte string, plaintext or unencrypted byte string
        """
        try:
            plaintext = self.cipher.decrypt_and_verify(ciphertext=self.ciphertext, received_mac_tag=self.tag)
            return plaintext
        except ValueError:
            return b''


class WalletDecrypt(Decrypt):
    pass