#
# A Chain Ratchet is expect to ensure that we do not sign different
# transactions at the same level.  An implementation of Chain Ratchet
# stores the level of the last successful transaction for each signature
# type(sig_type).  The check() method is passed the level of the incoming
# request, if it is higher than the stored level then the stored level
# is updated and True is returned. Otherwise, we return false.
#
# NOTE: the code that inherits from ChainRatchet is expected to
#       keep self.lastlevel and self.lastround up to date before
#       calling check().


class ChainRatchet:
    def check(self, sig_type, level=0, round=0):
        if self.lastlevel < level:
            return True
        if self.lastlevel == level and self.lastround < round:
            return True
        return False

#
# What follows is a mockery of a ChainRatchet.  It stores the level
# in memory and is useful only for testing.

class MockChainRatchet(ChainRatchet):

    def __init__(self, level=0, round=0):
        self.lastlevel = level
        self.lastround = round

    def check(self, sig_type, level=0, round=0):
        if not super().check(sig_type, level, round):
            return False
        self.lastlevel = level
        self.lastround = round
        return True
