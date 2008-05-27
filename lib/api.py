"""
    Provide the API interface for the various daemons.

    A daemon's API consists of a module containg two kinds of functions (name-prefix):
        xmlrpc_*
        http_*

    Both kinds of functions take a Context object as an argument, plus an arbitrary number of arguments (for xmlrpc, these are positional, for http
    these are keyword-arguments, but both should be considered).

    We accept queries from three sources (only the first two are implemented) :
        XMLRPC calls
        HTTP requests
        Internal Python function calls
"""

from twisted.internet import reactor
from twisted.web import xmlrpc, resource, server

from twisted.internet.defer import returnValue, inlineCallbacks, maybeDeferred

import traceback, sys

class FaultInfo (xmlrpc.Fault) :
    def __init__ (self, code, name, description) :
        self.code = code
        self.name = name
        self.description = description

        xmlrpc.Fault.__init__(self, code, "[%s] %s" % (self.name, self.description))

    def fault (self, audit_id) :
        return xmlrpc.Fault(self.code, "(%d) [%s] %s" % (audit_id, self.name, self.description))

def fault (code, name, description) :
    """
        Define a new fault type.

        Returns a function that, when called, will create and return a new FaultInfo object with the given code and string
    """

    def _fault () :
        return FaultInfo(code, name, description)
    
    return _fault

# after method fault
import api_errors as errors

class Context (object) :
    """
        The common context provided to xmlrpc/http method calls
    """

    # the API method name
    method = None

    # the remote client's IP address (note: v4 or v6)
    client = None

    # a string describing how the request was authenticated
    # <auth_method>:<auth_username>
    auth_info = None

    auth_method = None
    auth_user = None
    
    # set by Logger.api_audit
    # audit_id
    
    # set to True by dontLogResult to skip result-logging
    _dontLogResult_flag = False

    def _prepare (self) :
        self.auth_info = "%s:%s" % (self.auth_method, self.auth_user)

    def getAuthMethod (self) :
        """
            Get the method used to authenticate the request
        """

        return self.auth_method

    def getAuthUsername (self) :
        """
            Get the username used to authenticate
        """
        
        return self.auth_user

    def getClient (self) :
        """
            Get the ip address of the remote client
        """

        return self.client
    
    def dontLogResult (self) :
        self._dontLogResult_flag = True


class XMLRPCHandler (xmlrpc.XMLRPC) :
    """
        The handler for (all) XMLRPC requests

        We extend the XMLRPC method format slightly to allow for authentication.

        Instead of a single set of arguments, we receive an (auth_info, args) tuple. The contents of auth_info is used 
        for authentication purposes, and the contents of args (which may possibly be inspected for auth purposes as well
        if the method flags itself to require that) are passed to the method function.

        The return format needs some work as well. Perhaps (do we want to include logs/debug output in the return value?)

    """

    def __init__ (self, api) :
        self.api = api

        xmlrpc.XMLRPC.__init__(self)
    
    def _getFunction (self, func_name) :
        """
            Locate the given function by name
        """

        func = self.api._findXMLRPCFunction(func_name)

        if not func :
            raise xmlrpc.NoSuchFunction(self.NOT_FOUND, "function %s not found" % func_name)

        return self._requestHandler(func_name, func)
    
    def render_POST (self, request) :
        """
            Wrap xmlrpc.XMLRPC.render_POST to get our hands on the request object
        """

        self._current_request = request

        return xmlrpc.XMLRPC.render_POST(self, request)

    def _requestHandler (self, func_name, func) :
        @inlineCallbacks
        def _wrapper (*args) :
            if len(args) != 2 or not (isinstance(args[0], list) and isinstance(args[1], list)) or not args[0] :
                raise errors.Request_Format()
            
            # handle the auth data
            auth_data, func_args = args
            
            auth_method = auth_data.pop(0)

            auth_func = getattr(self, "auth_%s" % auth_method, None)

            if not auth_func :
                raise errors.Auth_Method()
            
            # build the context
            ctx = Context()
            ctx.method = func_name
            ctx.client = self._current_request.getClientIP()
            ctx.request = self._current_request
            ctx.auth_method = auth_method

            # this raises a fault on error
            auth_func(ctx, auth_data, args)

            # we have now authenticaticated
            ctx._prepare()

            # XXX: audit logs here?
            
            # now, call the method itself
            try :
                # it's deferred...
                ret_value = yield func(ctx, *func_args)

            except FaultInfo, e :
                # the method handled an error gracefully and raised an appropriate FaultInfo
                
                # log it to the db
                yield self.api.logger.api_log(ctx, "result:fault", (e.code, e.name))
                
                # return the fault complete with audit id
                raise e.fault(getattr(ctx, 'audit_id', -1))
            
            except Exception, e :
                # the method encountered an error which it couldn't handle...

                # log it to stderr
                # XXX: Needs some more info from ctx
                
                print >>sys.stderr, """\
Error while handling method call %s%r for %s from %s :
\t%s
                """ % (ctx.method, tuple(func_args), ctx.auth_info, ctx.client,
                        "\n\t".join(line for line in traceback.format_exc().split('\n')))
                
                # return a generic "Internal error"
                raise errors.Internal()
            
            if not ctx._dontLogResult_flag :
                yield self.api.logger.api_log(ctx, "result:ok", ret_value)

            # ...what's our return format?
            returnValue( ret_value )

        return _wrapper
    
    def auth_plain (self, ctx, auth_data, args) :
        if len(args) != 2 :
            raise errors.Auth_Format()

        ctx.auth_user, password = auth_data

        ctx.auth_value = self.api._checkAuth(ctx.auth_user, password)
    
class HTTPHandler (resource.Resource) :
    """
        The handler for a specific HTTP resource
    """

    def __init__ (self, api, name, func) :
        self.api = api
        self.name = name
        self.func = func

    def render (self, request) :
        #XXX: handle GET/POST differently?

        # just default to anon-auth for now
        auth_method = request.args.pop("auth_method", "anonymous")
        
        auth_func = getattr(self, "auth_%s" % auth_method, None)

        if not func :
            raise errors.Auth_Method()

        ctx = Context()
        ctx.method = self.name
        ctx.client = request.getClientIP()
        ctx.request = request
        ctx.auth_method = auth_method

        # this raises a fault on error
        auth_func(ctx, request.args)

        # we are authenticated
        ctx._prepare()

        return self.func(ctx, **dict((key, val[0] if len(val) == 1 else val) for key, val in request.args.iteritems()))

    def auth_anonymous (self, ctx, args) :
        ctx.auth_user = ctx.auth_password = ""
        ctx.auth_value = None
    
class APIServer (object) :
    def __init__ (self, api_module, settings_ns, auth_db, logger) :
        """
            Launch the API server for the given api module using the given settings
                xmlrpc_path         xmlrpc          the node in the root to use for XMLRPC requests
                http_port           -               the port to run the HTTP server on

            The format of the auth DB is not strictly specified yet - currently it should just be a dict of username -> password
        """
        self.api_module = api_module
        self.auth_db = auth_db
        self.logger = logger

        # settings
        self.http_xmlrpc_path = getattr(settings_ns, 'xmlrpc_path', "xmlrpc")
        self.http_port = getattr(settings_ns, 'http_port')
        
        # the HTTP resource tree root
        self.http_root = resource.Resource()
        
        # the XMLRPC handler
        self.http_root.putChild(self.http_xmlrpc_path, XMLRPCHandler(self))

        # the HTTP handlers
        self._buildHttpNodes()
        
        # the actual HTTP server
        self.http_site = server.Site(self.http_root)
        reactor.listenTCP(self.http_port, self.http_site)

    def _buildHttpNodes (self) :
        """
            Create a HTTPHandler instance for each http_* API function in the api module
        """

        for attr_name in dir(self.api_module) :
            if attr_name.startswith("http_") :
                http_func = getattr(self.api_module, attr_name)
                _, http_name = attr_name.split("_", 1)

                self.http_root.putChild(http_name, HTTPHandler(self, http_name, http_func))
    
    def _findXMLRPCFunction (self, name) :
        xmlrpc_name = "xmlrpc_%s" % name

        if not hasattr(self.api_module, xmlrpc_name) :
            return None

        return getattr(self.api_module, xmlrpc_name)
    
    def _checkAuth (self, username, password) :
        if username not in self.auth_db :
            raise errors.Auth_Username()

        if self.auth_db[username] != password :
            raise errors.Auth_Password()

        return True

