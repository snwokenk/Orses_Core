"""
Use this to provide a unified Protocol ID class

This avoids any conflict between the VerinodeListener and VeriNodeConnector Class.

A conflict my occur when an instance of Listener and Connector have the same Protocol Id
With This class, Each individual protocol will be guaranteed to have a unique protocol id
"""


class ProtoId:
    _protocol_id = 0

    @classmethod
    def protocol_id(cls):
        tmp = cls._protocol_id
        cls._protocol_id += 1
        return tmp
