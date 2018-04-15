"""
contains class for encrypting using AES256 and password key derivation

"""

from Crypto.Cipher import AES
from Crypto.Random import random
from getpass import getpass
import json


# import from created modules
from Orses_Cryptography_Core.PasswordKeyGeneration import PasswordKey


class Encrypt:
    def __init__(self, plaintext, password):
        """
        used to encrypt plaintext using AES-256 algorithm, pbkdf and password provided
        :param plaintext: byte string or encoded string, text to be encrypted
        :param password: string,
        """
        self.password = password
        self.salt = random.Random.urandom(16)
        self.key_object = PasswordKey(password=self.password, salt=self.salt)
        self.plaintext = plaintext
        self.cipher = AES.new(key=self.key_object.get_key(), mode=AES.MODE_EAX)

    def encrypt(self):
        """
        encrypts plaintext or self.plaintext
        :return: list, [ciphertext, tag, nonce, salt]
        """
        nonce = self.cipher.nonce
        ciphertext, tag = self.cipher.encrypt_and_digest(plaintext=self.plaintext)

        return [ciphertext.hex(), tag.hex(), nonce.hex(), self.salt.hex()]


class EncryptWallet(Encrypt):

    def __init__(self, wallet_instance,  password):
        super().__init__(plaintext=json.dumps(wallet_instance.get_wallet_details()).encode(), password=password)

    def encrypt(self):

        nonce = self.cipher.nonce
        ciphertext, tag = self.cipher.encrypt_and_digest(plaintext=self.plaintext)

        return [ciphertext.hex(), tag.hex(), nonce.hex(), self.salt.hex()]


if __name__ == '__main__':
    pass
    # key = random.Random.urandom(32)
    # cipher = AES.new(key=key, mode=AES.MODE_EAX)
    # nonce = cipher.nonce
    #
    # ciphertext, tag = cipher.encrypt_and_digest("Samuel".encode())
    #
    #
    #
    # cipher = AES.new(key=key, mode=AES.MODE_EAX, nonce=nonce)
    # plaintext = cipher.decrypt_and_verify(ciphertext=ciphertext, received_mac_tag=tag)
    #
    # print(plaintext)
