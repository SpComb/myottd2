from twisted.internet import protocol, stdio
from twisted.internet.defer import maybeDeferred

import traceback

"""
    Provides an interactive console on stdin/out for Twisted
"""

from curses_console import Console as CursesConsole, main as cursesMain

class StdioConsole (protocol.Protocol) :
    def __init__ (self) :
        self.readBuffer = ''
    
    def write (self, data) :
        self.transport.write(data)

    def writeLine (self, line) :
        self.transport.write("%s\n" % line)

    def dataReceived (self, data) :
        buf = self.readBuffer + data

        while '\n' in buf :
            line, buf = buf.split('\n', 1)

            self.lineReceived(line)

        self.readBuffer = buf

    def lineReceived (self, line) :
        pass

class CommandHandler (object) :
    """
        A console that reads in commands and handles them
    """

    def lineReceived (self, line) :
        if ' ' in line :
            cmd, data = line.split(' ', 1)
        else :
            cmd, data = line, ""

        d = maybeDeferred(self.commandReceived, cmd, data)

        d.addErrback(self._cmdErrHandler).addCallback(self._cmdDoneHandler)

    def _cmdErrHandler (self, failure) :
        self.error(failure.getTraceback())

    def _cmdDoneHandler (self, output) :
        if output :
            self.writeLine(output)
    
    def error (self, errmsg) :
        self.writeLine("ERROR: %s" % errmsg)

    def commandReceived (self, cmd, data) :
        if not cmd :
            return

        func = getattr(self, "cmd_%s" % cmd.lower(), None)

        if not func :
            self.error("Unknown command %r" % cmd)
            return

        return func(data)

def open (protocol_cls) :
    return stdio.StandardIO(protocol_cls())

