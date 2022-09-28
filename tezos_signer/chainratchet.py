#
# A Chain Ratchet is expect to ensure that we do not sign different
# transactions at the same level.  An implementation of Chain Ratchet
# stores the level of the last successful transaction for each signature
# type(sig_type).  The check() method is passed the level of the incoming
# request, if it is higher than the stored level then the stored level
# is updated and True is returned. Otherwise, we throw an exception
# specifying what went wrong.  Keep in mind that the text of the exception
# will be returned to the client and so be careful what you log locally
# versus what is exposed to clients.
#
# NOTE: the code that inherits from ChainRatchet is expected to
#       keep self.lastlevel and self.lastround up to date before
#       calling check().

from werkzeug.exceptions import abort

class ChainRatchet:
    def check(self, sig_type, level=0, round=0):
        if self.lastlevel < level:
            return True
        if self.lastlevel == level and self.lastround < round:
            return True
        abort(410, f"Will not sign {level}/{round} because ratchet " +
                   f"has seen {self.lastlevel}/{self.lastround}")

#
# What follows is a mockery of a ChainRatchet.  It stores the level
# in memory and is useful only for testing.

class MockChainRatchet(ChainRatchet):

    def __init__(self, config, level=0, round=0):
        self.lastlevel = level
        self.lastround = round

    def check(self, sig_type, level=0, round=0):
        super().check(sig_type, level, round)
        self.lastlevel = level
        self.lastround = round
        return True
