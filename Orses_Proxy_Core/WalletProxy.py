"""

This file will contain a class representing an instance of each proxy responsibility.

This means for each wallet this node is a proxy of, an instance of WalletProxy() will be used to manage the
responsibilities of the node to a wallet

Each walletProxy should have:

admin instance of main node
wallet id of Blockchain Connected Wallet
pubkey and private key unique

new_mode = If the proxy was just created then this is set to True but default is False

If WalletProxy represents a new proxy-bcw relationship then a new public/private key pair is created and public
key is returned. This public key is used by ProxyCenter to create a proxy acceptance msg, This message is stored under
the "WSH" section


"""

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Orses_Cryptography_Core.PKIGeneration import PKI


class WalletProxy:
    def __init__(self, proxy_center, bcw_wid: str, new_proxy=False, overwrite=False):
        self.admin_inst = proxy_center.admin_inst
        self.bcw_wid = bcw_wid
        self.bcw_filename = f"proxy_{bcw_wid}"
        self.bcw_proxy_pubkey = None
        self.bcw_proxy_privkey = None
        self.new_proxy = new_proxy
        self.overwrite = overwrite

        self.__set_or_create_pki_pair()

    def __set_or_create_pki_pair(self):

        # create an instance of PKI class (uses RSA 3072)
        pki = PKI(username=self.bcw_filename, password=self.admin_inst.password, user_instance=self)

        if self.new_proxy is True:
            pki.generate_pub_priv_key(
                save_in_folder=self.admin_inst.fl.get_proxy_folder_path(),
                overwrite=self.overwrite
            )

        self.bcw_proxy_pubkey = pki.load_pub_key(
            importedKey=False,
            x_y_only=True,
            user_or_wallet='wallet'  # use wallet, given WalletProxy acts similar to a wallet

        )
        self.bcw_proxy_privkey = pki.load_priv_key()

        if not self.bcw_proxy_privkey or not self.bcw_proxy_pubkey:
            print(f"In WalletProxy.py not able to load pubkey or privkey. might not exist") if self.new_proxy is False\
            else print(f"In WalletProxy.py not able to generate and load privkey or pubkey")

    def get_pubkey(self):

        if self.bcw_proxy_pubkey:
            return self.bcw_proxy_pubkey
        else:
            return {}

    def sign_a_message(self, msg: str):
        """
        used to sign a message
        :param msg:
        :return:
        """
