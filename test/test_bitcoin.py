from test.test_remote_signer import P256_SIG, RAW_SIGNED_BLOCK, SIGNED_BLOCK
from src.py3specials import bin_to_b58check

def test_pybitcointools():
    """
    make test TEST=test_pybitcointools
    """
    assert bin_to_b58check(RAW_SIGNED_BLOCK, magicbyte=P256_SIG) == SIGNED_BLOCK
