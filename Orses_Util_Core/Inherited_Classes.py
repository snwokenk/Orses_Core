"""
Use the classes in here to indirectly take advantage of Base class methods without having to import baseclass
Avoids some errors that comes in a "infinite loop import" where  module A imports Module B and
Module B imports Module A ( This throws an exception
"""


from Orses_Competitor_Core.Orses_Compete_Algo import Competitor, competitive_hasher, get_qualified_hashes
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData


competitive_hasher_func = competitive_hasher
get_qualified_hashes_func = get_qualified_hashes


class CompetitorInherited(Competitor):
    pass


class BlockChainDataInherited(BlockChainData):
    pass