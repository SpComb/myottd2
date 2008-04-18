from twisted.internet import protocol, reactor
from twisted.python import log
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
        return "RPC-API Authentication failed (%s)" % self.what

def authCheck (user, token, hash) :
    if user not in secrets :
        raise AuthError("user")

    my_hash = hashlib.sha1(secrets[user] + token).digest()

    if my_hash != hash :
        raise AuthError("hash")
    
    return True

class RPCAPI (rpc2.RPCProtocol) :
    def __init__ (self) :
        super(RPCAPI, self).__init__()

        self.auth_token = None

    def clientConnected (self) :
        log.msg("New client")
    
    # auth
    def hook_preCall (self, method, args) :
        if 'method' == 'auth_token_get' :
            return

        if len(args) < 2 :
            raise AuthError("args")

        user = str(args.pop(0))
        hash = str(args.pop(0))

        log.msg("Validate auth for user %s" % user)
        
        authCheck(user, self.auth_token, hash)
    
    def rpc_auth_token_get (self) :
        token = self.auth_token = generateAuthToken()

        log.msg("Our auth token is %s" % token)

        return token
    
    # stuff
    def rpc_daemon_status (self) :
        log.msg("rpc_daemon_status: OK")

        return "OK"

class RPCServer (protocol.ServerFactory) :
    def __init__ (self, port, proto, nexus) :
        self.protocol = proto
        self.nexus = nexus

        reactor.listenTCP(port, self)

RPC_PORT = 6905

def main () :
    import sys
    log.startLogging(sys.stdout)

    log.msg("Creating RPC Server...")
    rpc_server  = RPCServer(RPC_PORT, RPCAPI, None)
    
    log.msg("Starting reactor...")
    reactor.run()

if __name__ == '__main__' :
    main()


