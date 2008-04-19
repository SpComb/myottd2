from twisted.web import xmlrpc, server

from secrets import secrets
from lib.xmlrpc_auth import auth as _auth
from lib.mlogd import log

import settings

def auth (func) :
    return _auth(secrets)(func)

def log_audit (...) :
    ...

class XMLRPC_API (xmlrpc.XMLRPC) :
    @auth
    def xmlrpc_create_server (self, owner_id, srv_class) :
        ...

        return server_id
    
    @auth
    def xmlrpc_server_status (self, server_id) :
        ...

        return is_mounted, is_running, uptime_desc, load_avg_desc
    
    @auth
    def xmlrpc_mount_server (self, server_id) :
        ...

        return True
    
    @auth
    def xmlrc_update_server_version (self, server_id) :
        ...

        return True
    
    @auth
    def xmlrpc_start_server (self, server_id) :
        ...

        return True
    
    @auth
    def xmlrpc_stop_server (self, server_id) :
        ...

        return True
    
    @auth
    def xmlrpc_destroy_server (self, version_id) :
        ...

        return True

def main () :
    from twisted.internet import reactor

    r = XMLRPC_API()

    reactor.listenTCP(6905, server.Site(r))
    reactor.run()

if __name__ == '__main__' :
    main()

