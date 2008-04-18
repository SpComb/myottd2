from twisted.internet import protocol, defer
from twisted.python import failure, log

import buffer

class RPCError (Exception) :
    pass

class RPCProtocol (buffer.StreamProtocol, protocol.Protocol, object) :
    # what command to use for sending errors
    ERROR_COMMAND = None

    SEND_COMMANDS = RECV_COMMANDS = [
        'call',
        'ret',
        'err'
    ]

    def __init__ (self) :
        super(RPCProtocol, self).__init__()

        self.calls = []

    def invoke (self, method, *args) :
        o = self.startCommand('call')
        
        o.writeVarLen('B', method)

        writeMany(o, args)

        self.send(o)

        d = defer.Deferred()

        self.calls.append(d)

        return d
    
    def processCommand (self, buf) :
        type = buf.readEnum(self.RECV_COMMANDS)

        type_func = getattr(self, "process_%s" % type)

        return type_func(buf)

    def process_ret (self, buf) :
        val = readItem(buf)

        self._popCall().callback(val)

    def process_err (self, buf) :
        desc = readItem(buf)

        self._popCall().errback(desc)

    def process_call (self, buf) :
        method = buf.readVarLen('B')

        args = readMany(buf)
        
        ret = None

        try :
            func = getattr(self, "rpc_%s" % method)

            self.hook_preCall(method, args)
            
            ret = func(*args)
        except Exception, e :
            self.handle_error(failure.Failure())

            return

        if isinstance(ret, defer.Deferred) :
            ret.addErrback(self.handle_error).addCallback(self.handle_result)
        else :
            self.handle_result(ret)

    def handle_result (self, ret) :
        buf = self.startCommand('ret')

        writeItem(buf, ret)

        self.send(buf)

    def handle_error (self, failure) :
        log.err("Error in RPC command handler:")
        failure.printBriefTraceback()

        buf = self.startCommand('err')

        writeItem(buf, failure.getErrorMessage())

        self.send(buf)
    
    def hook_preCall (self, method, args) :
        """
            This is called with the method name and the given arguments before the method itself is called.

            The argument list may be modified
        """

        pass

    def error (self, error) :
        o = self.startCommand(self.ERROR_COMMAND)

        self._write_item(o, str(error))

        self.send(o)

    def _popCall (self) :
        return self.calls.pop(0)

def writeMany (buf, items) :
    buf.writeStruct('B', len(items))

    for item in items :
        writeItem(buf, item)

def writeItem (buf, arg) :
    if isinstance(arg, int) :
        if arg >= 0 :
            if arg < 2**8 :
                type = 'B'
            elif arg < 2**16 :
                type = 'H'
            elif arg < 2**32 :
                type = 'I'
            else :
                raise ValueError("Integer %d is too large" % arg)
        else :
            raise ValueError("Signed integers like %s are not yet supported" % arg)

        buf.write(type)   
        buf.writeStruct(type, arg)

    elif isinstance(arg, basestring) :
        if isinstance(arg, unicode) :
            arg = arg.encode('utf8')

        if len(arg) < 2**8 :
            type = 'B'
        elif len(arg) < 2**16 :
            type = 'H'
        elif len(arg) < 2**32 :
            type = 'I'
        else :
            raise ValueError("String of length %d is too long" % len(arg))

        buf.write('S')
        buf.write(type)
        buf.writeVarLen(type, arg)
    
    elif isinstance(arg, (tuple, list, dict)) :
        if isinstance(arg, dict) :
            arg = arg.iteritems()

        buf.write("X")
        writeMany(buf, arg)
    
    elif isinstance(arg, bool) :
        buf.write("x")
        buf.writeStruct('B', bool)

    elif arg is None :
        buf.write(" ")

    else :
        raise ValueError("Don't know how to handle argument of type %s" % type(arg))

def readMany (i) :
    num_args, = i.readStruct('B')

    args = []

    for x in xrange(num_args) :
        item = readItem(i)

        args.append(item)
    
    return args

def yieldUntilFalse (func, *args) :
    """
        This simply calls func with args, yielding whatever it returns as long
        as it evaluates to true. Once it returns something that evaluates to
        False, we stop iterating
    """

    while True :
        value = func(*args)

        if value :
            yield value
        else :
            return

def readItem (i) : 
    type = i.read(1)

#    print "Read type %r" % type

    if type == 'x' :
        value = bool(i.readStruct('B'))

    elif type == 'X' :
        value = readMany(i)

    elif type == 'S' :
        strType = i.read(1)

#        print "Str type %r" % strType

        value = i.readVarLen(strType)

    elif type == ' ' :
        value = None

    elif type == '(' :
        # variable-length list
        value = []
        
        while True :
            try :
                value.append(readItem(i))
            except StopIteration :
                break
    
    elif type == ')' :
        raise StopIteration()

    elif type == '@' :
        value = ''.join(yieldUntilFalse(i.readVarLen, 'B'))

    elif type == '!' :
        raise Exception(readItem(i))

    else :
        value = i.readItem(type)
    
    return value

