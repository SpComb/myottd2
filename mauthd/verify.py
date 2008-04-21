from twisted.internet.defer import returnValue, inlineCallbacks
import random, time, os, hashlib

from lib import utils
import settings, email

def generateToken (uid, username, pwhash, email) :
    """
        Generate a unique token based on the given arguments

        This is an md5 hash (hexadecimal format, 32 bytes)
    """

    # this should be "unique enough"...
    base = "%d%d%s%d%d%s%s%d" % (random.getrandbits(128), os.getpid(), username, uid, time.time(), pwhash, email, random.getrandbits(128))

    token = hashlib.md5(base).hexdigest()

    return token

@inlineCallbacks
def check_verify (uid, token) :
    """
        Check the given verification action. If it succeeds, the verification url should be invalidated,
        and the account marked as verified.

        This returns a simple string containing a message to show to the user

        Returns a (redirect_url, message) tuple. The message should be shown to the user,
        and if redirect_url is not None, the user should be redirected to that url.
    """

    verify_ok, user_ok, user_verified, username, success_url = yield db.find_verify(uid, token)
    
    if verify_ok :
        success_url = utils.build_url(success_url,
            uid         = uid,
            username    = username,
        )

        returnValue( success_url, "Account '%s' successfully activated" % (username))
    else :
        if not user_ok :
            returnValue( None, "No such user. Perhaps the verification email has already expired?")
        elif not user_verified :
            returnValue( None, "Bad token. Are you sure you have the entire link from the email correctly?")
        else :
            returnValue( None, "User has already been verified!")

