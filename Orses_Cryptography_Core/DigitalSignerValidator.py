from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

import base64

class DigitalSignerValidator:

    def __init__(self,  pubkey):
        """
        used to validate signature of message
        :param pubkey:
        """
        self.pubkey = None
        self.__import_pubkey(pubkey)

    def __import_pubkey(self, pubkey):
        """
        creates an rsa pub key object and sets self.pubkey to it
        :param pubkey: hex or bytes representation of key
        :return: None
        """
        try:
            self.pubkey = RSA.importKey(bytes.fromhex(pubkey))
        except TypeError:
            if isinstance(pubkey, bytes):
                self.pubkey = RSA.importKey(pubkey)

    def validate(self, message, signature):
        """
        used to validate signature
        :param message: string or byte string, message to validate signature(assignment statements, token transfers etc)
        :param signature: bytes string or hex string
        :return:
        """
        if self.pubkey is None or not isinstance(message, (str, bytes)):
            return ''
        elif not isinstance(signature, (str, bytes)):
            return ''



        try:
            hash_of_message = SHA256.new(message)
        except TypeError:
            hash_of_message = SHA256.new(message.encode())
        if isinstance(signature, str):
            signature = bytes.fromhex(signature)

        try:
            pkcs1_15.new(self.pubkey).verify(hash_of_message, signature=signature)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def validate_wallet_signature(msg, wallet_pubkey, signature):


        signature = signature.encode()
        signature = base64.b85decode(signature)

        if isinstance(wallet_pubkey, bytes):
            wallet_pubkey = RSA.importKey(wallet_pubkey)

        # if it a string
        try:
            hash_of_message = SHA256.new(msg)
        except TypeError:
            hash_of_message = SHA256.new(msg.encode())

        try:
            pkcs1_15.new(wallet_pubkey).verify(hash_of_message, signature=signature)
        except ValueError:
            return False
        else:
            return True



