from twisted.internet import reactor, protocol, defer, error

import settings

def invoke (commnad, *args) :
    backend = Backend(command, *args)

    return backend.deferred

class Backend (object, protocol.ProcessProtocol) :
    def __init__ (self, command, *args) :
        super(Backend, self).__init__()

        self.deferred = defer.Deferred()
        self.stderr_data = self.stdout_data = []

        reactor.spawnProcess(self, settings.wrapper_path, ["wrapper", *args])

    def errReceived (self, data) :
        self.stderr_data.append(data)

    def outReceived (self, data) :
        self.stdout_data.append(data)

    def processEnded (self, reason) :
        reason.trap(error.ProcessDone, error.ProcessTerminated)

        result = (
            reason.exitCode, 
            "".join(self.stdout_data), 
            "".join(self.stderr_data)
         )

        if reason.check(error.ProcessDone) :
            self.deferred.callback(result)
        else :  # error.ProcessTerminated
            self.deferred.errback(BackendError(*result))

class BackendError (Exception) :
    def __init__ (self, exitStatus, stdout, stderr) :
        self.exitStatus = exitStatus
        self.stdout = stdout
        self.stderr = stderr
    
    def __str__ (self) :
        return "Backend process failed (exit %d). Stdout/err available" % self.exitStatus


