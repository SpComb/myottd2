from twisted.internet import protocol, reactor
import random, hashlib

from lib import rpc2
from secrets import secrets
import api

AUTH_TOKEN_RAND_BITS = 123
def authGenerateToken () :
    return random.getrandbits(AUTH_TOKEN_RAND_BITS)

class AuthError (Exception) :
    def __init__ (self, what) :
        self.what = what

    def __str__ (self) :
        return "RPC-API Authentication failed (%s)" % what

def authCheck (user, token, hash) :
    if user not in secrets :
        raise AuthError("user")

    my_hash = hashlib.sha1(secrets[user] + token).digest()

    if my_hash != hash :
        raise AuthError("hash")
    
    return True

class API (rpc2.RPCProtocol) :
    def __init__ (self) :
        super(API, self).__init__()

        self.auth_token = None
    
    # auth
    def hook_preCall (self, method, args) :
        if 'method' == 'auth_token_get' :
            return

        user = str(args.pop(0))
        hash = str(args.pop(0))
        
        authCheck(user, self.auth_token, hash)
    
    def rpc_auth_token_get (self) :
        token = self.auth_token = generateAuthToken()

        return token
    
    # stuff
    def rpc_daemon_status (self) :
        return "OK"

