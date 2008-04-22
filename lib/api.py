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

class Context (object) :
    """
        The common context provided to xmlrpc/http method calls
    """

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

class Fault (xmlrpc.Fault) :
    faultCode = 8999
    faultString = None

    def __init__ (self) :
        if not self.faultString :
            self.faultString = str(self)

        xmlrpc.Fault(self.faultCode, self.faultString)

class AuthFormatError (Fault) :
    def __init__ (self, what) :
        self.faultString = self.faultString % what

        Fault.__init__(self)

    faultCode = 8111
    faultString = "Invalid format of authentication/argument data (%s)"

class AuthMethodError (Fault) :
    faultCode = 8112
    faultString = "Invalid authentication method"

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
    
    def _getFunction (self, functionPath) :
        """
            Locate the given function by name
        """

        func = self.api._findXMLRPCFunction(functionPath)

        if not func :
            raise xmlrpc.NoSuchFunction(self.NOT_FOUND, "function %s not found" % functionPath)

        return self._requestHandler(functionPath, func)
    
    def render_POST (self, request) :
        """
            Wrap xmlrpc.XMLRPC.render_POST to get our hands on the request object
        """

        self._current_request = request

        return xmlrpc.XMLRPC.render_POST(self, request)

    def _requestHandler (self, name, func) :
        def _wrapper (*args) :
            if len(args) != 2 or not (isinstance(args[0], list) and isinstance(args[1], list)) or not args[0] :
                raise AuthFormatError("auth/args tuples")
            
            # handle the auth data
            auth_data, func_args = args
            
            auth_method = auth_data.pop(0)

            auth_func = getattr(self, "auth_%s" % auth_method, None)

            if not func :
                raise AuthMethodError()
            
            # build the context
            ctx = Context()
            ctx.request = self._current_request
            ctx.client = ctx.request.getClientIP()
            ctx.auth_method = auth_method

            # this raises a fault on error
            auth_func(ctx, auth_data, args)


            # we have now authenticaticated

            # XXX: audit logs
            
            # now, call the method itself
            ret_value = func(ctx, *func_args)
            
            # ...what's our return format?
            return ret_value

        return _wrapper
    
    def auth_plain (self, ctx, auth_data, args) :
        if len(args) != 2 :
            raise AuthFormatError("auth_data")

        ctx.auth_user, ctx.auth_password = auth_data

        ctx.auth_value = self.api._checkAuth(ctx.auth_user, ctx.auth_password)
    
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
            raise AuthMethodError()

        ctx = Context()
        ctx.request = request
        ctx.client = request.getClientIP()
        ctx.auth_method = auth_method

        # this raises a fault on error
        auth_func(ctx, request.args)

        # we are authenticated

        return self.func(ctx, **dict((key, val[0] if len(val) == 1 else val) for key, val in request.args.iteritems()))

    def auth_anonymous (self, ctx, args) :
        ctx.auth_user = ctx.auth_password = ""
        ctx.auth_value = None
    
class AuthUsernameError (Fault) :
    faultCode = 8121
    faultString = "Authentication error (Username)"

class AuthPasswordError (Fault) :
    faultCode = 8122
    faultString = "Authentication error (Password)"

class APIServer (object) :
    def __init__ (self, api_module, settings_ns, auth_db) :
        """
            Launch the API server for the given api module using the given settings
                xmlrpc_path         xmlrpc          the node in the root to use for XMLRPC requests
                http_port           6910            the port to run the HTTP server on

            The format of the auth DB is not strictly specified yet - currently it should just be a dict of username -> password
        """
        self.api_module = api_module
        self.auth_db = auth_db

        # settings
        self.http_xmlrpc_path = getattr(settings_ns, 'xmlrpc_path', "xmlrpc")
        self.http_port = getattr(settings_ns, 'http_port', 6910)
        
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
            raise AuthUsernameError()

        if self.auth_db[username] != password :
            raise AuthPasswordError()

        return True

