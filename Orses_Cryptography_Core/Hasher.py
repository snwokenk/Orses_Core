from Crypto.Hash import SHA256, SHA512, RIPEMD160
import base64

class Hasher:
    def __init__(self):
        pass


    @staticmethod
    def sha_hasher(data: (str, bytes, ), hash_strength=256, hash_form="hex"):
        """

        :param data: data to be hashed str or bytes
        :type data: str
        :param hash_strength: strength of hash either 256 or 512
        :type hash_strength: int
        :param hash_form: format to return
        :type hash_form: str ('hex', 'b85_str')
        :return: hex or byte of hash
        """

        if not isinstance(data, (bytes, str)):
            data = str(data).encode()
        elif isinstance(data, str):
            data = data.encode()
        elif isinstance(data, bytes):
            pass

        if hash_strength == 512:
            h = SHA512.new(data)
        else:  # use SHA256
            h = SHA256.new(data)

        if hash_form.lower() == "hex":
            return h.hexdigest()
        elif hash_form.lower() == "b85_str":
            return base64.b85encode(h.digest()).decode()
        else:
            return h.digest()  # bytes


    @staticmethod
    def ripe160_hasher(data, hash_form="hex"):
        """
        used to hash data with RIPEMD160 algorithm
        :param data: data to be hashed
        :type data: str
        :param hash_form: format to return hash 'hex, or 'bytes' default is 'hex'
        :type hash_form: str
        :return: hex or bytes of hash
        """

        if not isinstance(data, (bytes, str)):
            data = str(data).encode()
        elif isinstance(data, str):
            data = data.encode()

        h = RIPEMD160.new(data)

        if hash_form == "hex":
            return h.hexdigest()
        elif hash_form == "b85_str":
            return base64.b85encode(h.digest()).decode()
        else:
            return h.digest()  # bytes


if __name__ == '__main__':
    d = "samuel"

    print(Hasher.ripe160_hasher(d, hash_form='byte'))