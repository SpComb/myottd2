from twisted.internet import reactor, protocol, defer, error

import settings

def invoke (command, *args) :
    backend = Backend(command, *args)

    return backend.deferred

class Backend (object, protocol.ProcessProtocol) :
    def __init__ (self, command, *args) :
        super(Backend, self).__init__()

        self.deferred = defer.Deferred()
        self.stderr_data = self.stdout_data = []

        self.output_lines = []
        self.stdout_buf = self.stderr_buf = ''

        reactor.spawnProcess(self, settings.wrapper_path, ["wrapper", command] + list(args))
    
    def _processData (self, type, data, buf) :
        buf += data

        while '\n' in buf :
            line, buf = buf.split('\n', 1)

            self.output_lines.append((type, line))

        return buf

    def errReceived (self, data) :
        self.stderr_buf = self._processData("stderr", data, self.stderr_buf)

    def outReceived (self, data) :
        self.stdout_buf = self._processData("stdout", data, self.stdout_buf)

    def processEnded (self, reason) :
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
    

