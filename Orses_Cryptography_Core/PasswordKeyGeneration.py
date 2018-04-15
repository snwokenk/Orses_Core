"""
contains class for deriving encryption key from password using pbkdf2 algorithm
"""

from Crypto.Protocol import KDF
from Crypto.Random import random

from CryptoHub_Util.FileAction import FileAction


class PasswordKey:
    def __init__(self, password, salt, desired_key_len=32):
        """

        :param password: string, must be string
        :param salt: bytes, must be bytes (will through a TypeError if not) but type error says must be string (flaw)
        :param desired_key_len: for AES256 key len is 32
        """
        self.password = password
        self.salt = salt
        self.lenght_of_key = desired_key_len

    def get_key(self):
        """
        :return:
        """

        key = KDF.PBKDF2(password=self.password, salt=self.salt, count=100000, dkLen=self.lenght_of_key)
        return key


if __name__ == '__main__':

    salt1 = random.Random.urandom(16)

    key = KDF.PBKDF2("7433xxxxxxx", salt=salt1, count=100000, dkLen=32)
    print(len(key))
    print(key)

