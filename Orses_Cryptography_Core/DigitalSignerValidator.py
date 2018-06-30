from Crypto.Signature import DSS
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
import base64


class DigitalSignerValidator:

    def __init__(self,  pubkey=None):
        """
        used to validate signature of message
        :param pubkey: For compability until refactor
        """



    @staticmethod
    def validate(msg, pubkey: dict, signature):
        """
        used to validate signature
        :param message: string or byte string, message to validate signature(assignment statements, token transfers etc)
        :param signature: bytes string or hex string
        :param pubkey: {"x": base85 string, "y": base85 string}  # use base64.b85decode(pubkey["x"}.encode) to get
                        pubkey bytes
        :type pubkey: dict
        :return:
        """
        if signature is None:
            print("Signature is None. probably cause something other than a string or byte being passed to signer")
            return False
        try:
            x_int = base64.b85decode(pubkey["x"].encode())
            x_int = int.from_bytes(x_int, "big")

            y_int = base64.b85decode(pubkey["y"].encode())
            y_int = int.from_bytes(y_int, "big")
        except KeyError:
            return False

        signature = signature.encode()
        signature = base64.b85decode(signature)

        # if it a string
        try:
            hash_of_message = SHA256.new(msg)
        except TypeError:
            hash_of_message = SHA256.new(msg.encode())

        try:
            pubkey = ECC.construct(point_x=x_int, point_y=y_int, curve="P-256").public_key()
            verifier = DSS.new(pubkey, mode="fips-186-3")
            verifier.verify(hash_of_message, signature=signature)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def validate_wallet_signature(msg, wallet_pubkey, signature):
        """

        :param msg:
        :param wallet_pubkey:
        :param signature:
        :return:
        """
        if signature is None:
            print("Signature is None. probably cause something other than a string or byte being passed to signer")
            return False
        try:
            x_int = base64.b85decode(wallet_pubkey["x"].encode())
            x_int = int.from_bytes(x_int, "big")

            y_int = base64.b85decode(wallet_pubkey["y"].encode())
            y_int = int.from_bytes(y_int, "big")
        except KeyError:
            return False

        signature = signature.encode()
        signature = base64.b85decode(signature)

        # if it a string
        try:
            hash_of_message = SHA256.new(msg)
        except TypeError:
            hash_of_message = SHA256.new(msg.encode())

        try:
            wallet_pubkey = ECC.construct(point_x=x_int, point_y=y_int, curve="P-256").public_key()
            verifier = DSS.new(wallet_pubkey, mode="fips-186-3")
            verifier.verify(hash_of_message, signature=signature)
        except ValueError:
            return False
        else:
            return True



