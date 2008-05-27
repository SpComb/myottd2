from twisted.internet import protocol, reactor, interfaces, defer
from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from lib import fifo2, buffer as streamModule, console as consoleModule

def parse_struct (data) :
    tuples = [(cmd.strip(), eval(code.strip())) for cmd, code in (line.strip().split("=") for line in data.strip().split(",") if line)]

    return dict(tuples), dict((code, cmd) for (cmd, code) in tuples)

cmd2code, code2cmd = parse_struct("""
    CMD_INOUT_HELLO         = 0x01,
    CMD_OUT_ERROR           = 0x02,
    CMD_OUT_REPLY           = 0x03,

    CMD_OUT_DATA_STDOUT     = 0x10,
    CMD_OUT_DATA_STDERR     = 0x11,

    CMD_OUT_STATUS          = 0x20,

    CMD_IN_DATA_STDIN       = 0x60,

    CMD_IN_DO_START         = 0x70,
    CMD_IN_DO_KILL          = 0x71,

    CMD_IN_QUERY_STATUS     = 0x80,

    CMD_MAX                 = 0xFF,
""")

err2code, code2err = parse_struct("""
    ERROR_INVALID_STATE     = 0x0001,
    ERROR_INVALID_CMD       = 0x0002,
    ERROR_INVALID_CMD_STATE = 0x0003,
    ERROR_SHORT_CMD_DATA    = 0x0004,

    ERROR_CMD_ARGS_SIZE             = 0xA101,

    ERROR_CMD_PROCESS_INTERNAL      = 0xA201,
    ERROR_PROCESS_NOT_RUNNING       = 0xA202,
    ERROR_PROCESS_ALREADY_RUNNING   = 0xA203,

    ERROR_CMD_START_ARGS_COUNT      = 0x7002,
""")

reply2code, code2reply = parse_struct("""
    REPLY_SUCCESS           = 0x0000,   
    
    REPLY_HELLO             = 0x0100,
    
    REPLY_STATUS_IDLE       = 0x8000,
    REPLY_STATUS_RUN        = 0x8001,
    REPLY_STATUS_EXIT       = 0x8002,   
    REPLY_STATUS_KILLED     = 0x8003,  
    REPLY_STATUS_ERR        = 0x80FF,   
""")

class Console (consoleModule.CommandHandler, consoleModule.CursesConsole) :
    # the control channel
    control = None

    def __init__ (self, stdscr) :
        # because otherwise we have object's __init__ here
        consoleModule.CursesConsole.__init__(self, stdscr)

    def preConnect (self) :
        self.writeLine("Connecting to process daemon...")
    
    def onConnected (self) :
        self.writeLine("Connected, sending hello...")
    
    def helloFailed (self, failure) :
        self.writeLine("Hello failed: %s" % failure.value)

    def onHello (self, version) :
        self.writeLine("Connection OK, remote protocol version 0x%02X" % version)

    def controlConnectionLost (self, reason) :
        self.error("Control connection lost: %r" % reason)
    
    def onStatus (self, status, data) :
        self.writeLine("Process changed status: %s %d" % (status, data))

    def gotData (self, stream, data) :
        self.writeLine("[%s] %s" % (stream, data))

    def gotEOF (self, stream) :
        self.writeLine("[%s] <EOF>" % (stream, ))
    
    @inlineCallbacks
    def cmd_status (self, data) :
        self.writeLine("Sending status query...")
        code, data = yield self.control.queryStatus()

        returnValue( "status: %s: %s" % (code, data) )
    
    @inlineCallbacks
    def cmd_start (self, data) :
        args = data.split()

        self.writeLine("Sending start command...")

        success = yield self.control.sendStart(args)

        returnValue( "start: %s" % success )
    
    @inlineCallbacks
    def cmd_write (self, data) :
        self.writeLine("Sending data...")

        success = yield self.control.sendData("%s\n" % data)

        returnValue( "write: %s" % success )

    @inlineCallbacks
    def cmd_kill (self, data) :
        signal = int(data)

        self.writeLine("Sending signal %d..." % signal)

        success = yield self.control.sendSignal(signal)

        returnValue( "kill: %s" % success )

    def cmd_quit (self, data) :
        self.writeLine("Closing connection...")
        self.control.transport.loseConnection()

class ProtocolError (Exception) :
    def __init__ (self, err) :
        self.err = err

    def __str__ (self) :
        return "Protocol Error: %s" % self.err

class ControlProtocol (streamModule.StreamProtocol, protocol.Protocol) :
    PROTOCOL_VERSION = 0x01

    def __init__ (self) :
        super(ControlProtocol, self).__init__()

        self.requestDeferreds = []
    
    def connectionMade (self) :
        self.writer = streamModule.WriteTransport(self.transport)

        self.sendVersion().addCallback(self.gotHello).addErrback(self.helloFailed)

    def processCommand (self, stream) :
        cmd = stream.readEnum(code2cmd)
        data = streamModule.ReadBuffer(stream.readVarLen('B'), strictRead=True)

        func = getattr(self, cmd.lower())

        func(data)
    
    def sendCommand (self, command, data) :
        self.writer.writeEnum(cmd2code, command)
        self.writer.writeVarLen("B", data)

        deferred = defer.Deferred()

        self.requestDeferreds.append(deferred)

        return deferred
    
    def cmd_out_reply (self, dataStream) :
        code = dataStream.readEnum(code2reply, 'H')
        data = dataStream.readItem("H")

        deferred = self.requestDeferreds.pop(0)

        deferred.callback((code, data))

    def cmd_out_error (self, dataStream) :
        error = dataStream.readEnum(code2err, 'H')

        deferred = self.requestDeferreds.pop(0)

        deferred.errback(ProtocolError(error))

    def cmd_out_status (self, dataStream) :
        status = dataStream.readEnum(code2reply, 'H')
        data = dataStream.readItem('H')

        self.gotStatus(status, data)

    def cmd_out_data_stdout (self, dataStream) :
        data = dataStream.getvalue()

        self.gotStdoutData (data)

    def cmd_out_data_stderr (self, dataStream) :
        data = dataStream.getvalue()

        self.gotStderrData (data)
    
    # handle events
    def gotHello (self, version) :
        pass
    
    def gotStatus (self, status, data) :
        pass

    def gotStdoutData (self, data) :
        pass

    def gotStderrData (self, data) :
        pass

    # do stuff
    def sendVersion (self) :
        buf = streamModule.WriteBuffer()
        buf.writeStruct("B", self.PROTOCOL_VERSION)

        return self.sendCommand("CMD_INOUT_HELLO", buf.getvalue()).addCallback(self._sendVersion_result)

    def _sendVersion_result (self, (code, data)) :
        """
            Just return the version number
        """

        assert code == "REPLY_HELLO"

        return data

    def queryStatus (self) :
        """
            Get the process status
        """

        return self.sendCommand("CMD_IN_QUERY_STATUS", "")

    def sendStart (self, args) :
        """
            Attempt to start the process
        """
        
        data = streamModule.WriteBuffer()
            
        data.writeStruct('B', len(args))

        for arg in args :
            data.writeVarLen('B', arg)

        return self.sendCommand("CMD_IN_DO_START", data.getvalue()).addCallback(self._sendStart_result)

    def _sendStart_result (self, (code, data)) :
        """
            Just return the REPLY_SUCCESS
        """

        assert code == "REPLY_SUCCESS"

        return code
    
    def sendData (self, data) :
        """
            Send data to the process's stdin
        """

        assert len(data) <= 255
        
        return self.sendCommand("CMD_IN_DATA_STDIN", data).addCallback(self._sendData_result)

    def _sendData_result (self, (code, data)) :
        assert code == "REPLY_SUCCESS"

        return code

    def sendSignal (self, signal) :
        """
            Send a signal to the process
        """

        data = streamModule.WriteBuffer()

        data.writeStruct('B', signal)

        return self.sendCommand("CMD_IN_DO_KILL", data.getvalue()).addCallback(self._sendSignal_result)

    def _sendSignal_result (self, (code, data)) :
        assert code == "REPLY_SUCCESS"

        return code

class FifoProtocol (ControlProtocol) :
    implements(interfaces.IHalfCloseableProtocol)

    writePath = "test/daemon-in"
    readPath = "test/daemon-out"

    def __init__ (self) :
        super(FifoProtocol, self).__init__()
        
        self.fifoPair = fifo2.FifoPair(self, readPath=self.readPath, writePath=self.writePath)
        
    def readConnectionLost (self) :
        self.transport.loseConnection()

    def writeConnectionLost (self) :
        self.transport.loseConnection()

class ConsoleControlProtocol (FifoProtocol) :
    # the cosole we are linked with
    console = None

    def __init__ (self, console) :
        self.console = console

        self.stdoutReader = streamModule.LineReader()
        self.stderrReader = streamModule.LineReader()

        super(ConsoleControlProtocol, self).__init__()
    
    def connectionMade (self) :
        self.console.onConnected()
        
        super(ConsoleControlProtocol, self).connectionMade()
    
    def dataReceived (self, data) :
        super(ConsoleControlProtocol, self).dataReceived(data)
    
    def helloFailed (self, error) :
        self.console.helloFailed(error)

    def gotHello (self, version) :
        self.console.onHello(version)
    
    def gotStatus (self, status, data) :
        self.console.onStatus(status, data)
    
    def gotStdoutData (self, data) :
        if data :
            for line in self.stdoutReader.feed(data) :
                self.console.gotData('stdout', line)
        else :
            self.console.gotEOF('stdout')

    def gotStderrData (self, data) :
        if data :
            for line in self.stderrReader.feed(data) :
                self.console.gotData('stderr', line)
        else :
            self.console.gotEOF('stderr')

    def readConnectionLost (self) :
        self.console.controlConnectionLost("read")

    def writeConnectionLost (self) :
        self.console.controlConnectionLost("write")
    
    def connectionLost (self, reason) :
        self.console.controlConnectionLost(reason)

def main_init (console) :
    console.preConnect()
    
    control = ConsoleControlProtocol(console)
    console.control = control

def main () :
    consoleModule.cursesMain(Console, main_init)

if __name__ == '__main__' :
    main()

