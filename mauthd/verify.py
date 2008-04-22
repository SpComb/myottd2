from twisted.internet.defer import returnValue, inlineCallbacks
import random, time, os, hashlib

from lib import utils
import settings, email

def generateToken (username, pwhash, email) :
    """
        Generate a unique token based on the given arguments

        This is an md5 hash (hexadecimal format, 32 bytes)
    """

    # this should be "unique enough"...
    base = "%d%d%s%d%s%s%d" % (random.getrandbits(128), os.getpid(), username, time.time(), pwhash, email, random.getrandbits(128))

    token = hashlib.md5(base).hexdigest()

    return token

