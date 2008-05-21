from twisted.internet import abstract, fdesc, interfaces

import os

"""
    Support for handling FIFOs in twisted.

    Provides a ITransport that handles a read/write fifo pair
"""


class _BaseFD (abstract.FileDescriptor) :
    """
        Wraps around abstract.FileDescriptor to provide some basic conveniances.

        Represents a single OS fd.
    """

    def __init__ (self, fifo, reactor, fileno, readable=False, writeable=False) :
        abstract.FileDescriptor.__init__(self, reactor)
        fdesc.setNonBlocking(fileno)
        
        self.fifo = fifo

        self.fd = fileno

        # and yes, we are connected
        self.connected = True

        if readable :
            self.startReading()
        
        # we don't need to do this, called by abstract.FileDescriptor.write() as needed
        #if writeable :
        #    self.startWriting()
    
    def fileno (self) :
        return self.fd
    
    def connectionLost (self, reason) :
        self.close()

        self._connectionLost(reason)

    def close (self) :
        if self.fd :
            os.close(self.fd)
            self.fd = None

    def __del__ (self) :
        self.close()

class FifoReader (_BaseFD) :
    """
        Handles a read-FIFO
    """

    def __init__ (self, fifo, reactor, fileno) :
        _BaseFD.__init__(self, fifo, reactor, fileno, readable=True)

    def doRead (self) :
        return fdesc.readFromFD(self.fd, self.dataReceived)

    def dataReceived (self, data) :
        self.fifo.readDataReceived(data)

    def _connectionLost (self, reason) :
        self.fifo.readConnectionLost(reason)

class FifoWriter (_BaseFD) :
    """
        Handles a write-FIFO
    """

    def __init__ (self, fifo, reactor, fileno) :
        _BaseFD.__init__(self, fifo, reactor, fileno, writeable=True)

    def writeSomeData (self, data) :
        return fdesc.writeToFD(self.fd, data)
    
    def _connectionLost (self, reason) :
        self.fifo.writeConnectionLost(reason)

class FifoPair (object) :
    """
        Acts as a twisted transport for two linux FIFO files, one in read mode, the other in write mode.

        An given FIFO is always in either read or write mode - not both. However, this class lets you open one fifo for
        write, and one fifo for read simultaneously (or only one of them, of course).

        Fifo behaves like this :
            For reading :
                Opening the fifo succeeds immediately, and the protocol will be connected (connectionMade) right away.
                This does not, however, imply that anyone has the fifo open for writing.

                Once someone opens the fifo up for write and writes some data, this data will be delivered to the
                protocol's dataReceived method.
                
                If the fifo's write end is closed, I will receive an EOF on the fifo. How this is handled depends on
                the value of the "reopenOnEOF" argument; when False (default), I will call protocol.connectionLost(),
                and the transport is regarded as closed.  When True, I will call protocol.fifoEOF(), and then re-open
                the fifo, and I can be used again.
                
            For writing :
                Opening the fifo only succeeds if someone has the fifo open for read already.

                If the read-end of the fifo is closed, I will immediately undergo connectionLost.
                XXX: it seems this doesn't cause the fifo to select after all, the buggy behaviour?

    """

    def __init__ (self, protocol, readPath=None, writePath=None, reactor=None) :
        self.protocol = protocol
        self.reactor = reactor
        
        self.readPath = self.writePath = None
        self.read_fd_obj = self.write_fd_obj = None

        # we're supposed to open it right away
        self._openFifos(readPath, writePath)

        # since the OS doesn't really tell us if there's anyone on the end of a FIFO, we need to call this now
        #  r: we open it with os.O_NONBLOCK which succeeds right away, and the fd doesn't provide any signal if someone opens it for w
        #  w: if we manage to open it, there's someone reading on it.
        self.protocol.makeConnection(self)
    
    # methods to change state
    def _openFifos (self, readPath, writePath) :
        """
            Open the two read/write fifos as given (one of them may be None)
        """

        if not (readPath or writePath) :
            raise ValueError("Must specify at least one of readPath or writePath")

        if readPath :
            if self.readPath :
                raise Exception("read-fifo already opened")

            self.readPath = readPath
            self.read_fd_obj = self._open(readPath, os.O_RDONLY, FifoReader)

        if writePath :
            if self.writePath :
                raise Exception("write-fifo already opened")

            self.writePath = writePath
            self.write_fd_obj = self._open(writePath, os.O_WRONLY, FifoWriter)
        
    def _open (self, path, mode_flag, fd_obj_cls) :
        """
            Open the fifo at the given path with the given flags and instantate+return the given _BaseFD subclass
        """

        fd = os.open(path, mode_flag | os.O_NONBLOCK)

        fd_obj = fd_obj_cls(self, self.reactor, fd)

        return fd_obj
    
    def _closeFifos (self) :
        """
            Close open fifos
        """

        if self.write_fd_obj :
            self.write_fd_obj.close()
            self.write_fd_obj = None

        if self.read_fd_obj :
            self.read_fd_obj.close()
            self.read_fd_obj = None

    # methods for checking state
    def _checkReadable (self) :
        if not self.read_fd_obj :
            raise Exception("fifo is not readable")

    def _checkWriteable (self) :
        if not self.write_fd_obj :
            raise Exception("fifo is not writeable")

    # methods called by Fifo{Reader,Writer}
    def readDataReceived (self, data) :
        self.protocol.dataReceived(data)
    
    def readConnectionLost (self, reason) :
        self.read_fd_obj = None
        
        if self.write_fd_obj and interfaces.IHalfCloseableProtocol.providedBy(self.protocol) :
            self.protocol.readConnectionLost()
        else :
            self.protocol.connectionLost(reason)
            self._closeFifos()
    
    def writeConnectionLost (self, reason) :
        self.write_fd_obj = None

        if self.read_fd_obj and interfaces.IHalfCloseableProtocol.providedBy(self.protocol) :
            self.protocol.writeConnectionLost()
        else :
            self.protocol.connectionLost(reason)
            self._closeFifos()
    
    # ITransport methods
    def write (self, data) :
        self._checkWriteable()

        self.write_fd_obj.write(data)
    
    def writeSequence (self, iovec) :
        self._checkWriteable()
        
        self.write_fd_obj.writeSequence(iovec)
    
    def loseConnection (self) :
        if self.write_fd_obj :
            self.write_fd_obj.loseConnection()

        if self.read_fd_obj :
            self.read_fd_obj.loseConnection()
    
    def getPeer (self) :
        pass

    def getHost (self) :
        pass
    
    # extensions to ITransport
    def openFifo (self, readPath=None, writePath=None) :
        self._openFifos(readPath, writePath)

def open (proto, path, mode) :
    paths = dict(
        readPath = (mode == 'r') and path,
        writePath = (mode == 'w') and path,
    )

    return FifoPair(proto, **paths)

