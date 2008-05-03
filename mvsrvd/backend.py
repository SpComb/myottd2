from twisted.internet import reactor, protocol, defer, error

from lib import log

import settings

import os.path

def invoke (command, *args) :
    backend = Backend(command, *args)

    return backend.deferred

def server_state (context_id) :
    proc_info_path = "/proc/virtual/%d" % context_id
    
    is_running = os.path.exists(proc_info_path)

    return is_running

class Backend (object, protocol.ProcessProtocol) :
    def __init__ (self, command, *args) :
        super(Backend, self).__init__()

        self.deferred = defer.Deferred()
        self.stderr_data = self.stdout_data = []

        self.output_lines = []
        self.stdout_buf = self.stderr_buf = ''

        args = ["wrapper", command] + list(args)

        log.info("spawn process from `%s' with args: %s", settings.wrapper_path, args)

        reactor.spawnProcess(self, settings.wrapper_path, args)
    
    def _processData (self, type, data, buf) :
        buf += data

        log.debug("received data on %s: %s", type, data)

        while '\n' in buf :
            line, buf = buf.split('\n', 1)

            self.output_lines.append((type, line))

        return buf

    def errReceived (self, data) :
        self.stderr_buf = self._processData("stderr", data, self.stderr_buf)

    def outReceived (self, data) :
        self.stdout_buf = self._processData("stdout", data, self.stdout_buf)

    def childConnectionLost (self, fd) :
        log.info("process connection lost on fd %s", fd)

    def processEnded (self, reason) :
        log.info("process ended: %r", reason)

        reason.trap(error.ProcessDone, error.ProcessTerminated)
        
        exit_code = reason.value.exitCode
        output = self.output_lines

        if reason.check(error.ProcessDone) :
            self.deferred.callback((exit_code, output))
        else :  # error.ProcessTerminated
            self.deferred.errback(BackendError(exit_code, output))

class BackendError (Exception) :
    def __init__ (self, exitStatus, output) :
        self.exitStatus = exitStatus
        self.output = output
    

