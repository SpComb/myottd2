from twisted.internet import protocol, reactor, defer
import rpc2

class RPCClient (rpc2.RPCProtocol) :
    def connectionMade (self) :
        self.factory.haveRPC(self)

class RPCCallFactory (protocol.ClientFactory) :
    protocol = RPCClient

    def __init__ (self, host, port, method, *args) :
        reactor.connectTCP(host, port, self)

        self.call = (method, args)

        self.d = defer.Deferred()

    def clientConnectionFailed (self, connector, failure) :
        if self.d :
            self.d.errback(failure)
            self.d = None
    
    clientConnectionLost = clientConnectionFailed
     
    def haveRPC (self, proto) :
        self.rpc = proto
        
        method, args = self.call

        self.rpc.invoke(method, *args).chainDeferred(self.d)

def RPCCall (host, port, method, *args) :
    cf = RPCCallFactory(host, port, method, *args)

    return cf.d

def main (host, port, method, args) :
    print "%s:%d - %s%r" % (host, port, method, args)
    RPCCall(host, port, method, *args).addCallback(main_gotResult).addErrback(main_gotFailure)
    print "---"

    reactor.run()

def main_gotResult (result) :
    print repr(result)

    reactor.stop()

def main_gotFailure (failure) :
    print failure.getErrorMessage()
    
    reactor.callLater(0, reactor.stop)

if __name__ == '__main__' :
    from sys import argv

    host = argv.pop(1)
    port = int(argv.pop(1))
    method = argv.pop(1)
    args = tuple(argv[1:])

    main(host, port, method, args)

