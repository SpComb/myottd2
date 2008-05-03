from twisted.internet.defer import returnValue, inlineCallbacks

from lib import utils, api, log
import db, backend, settings, errors

from lib import log as _log

log = _log.Logger("vserver", db.db)

@inlineCallbacks
def xmlrpc_initialize_server (ctx, server_id) :
    """
        Initialize a server, creating the vserver and updating the database

        A row for the given server_id must already exist in the database, this method will allocate a new location (ip, port, ctx) for the
        server and update the server accordingly.
    """

    yield log.api_audit(ctx, server_id)

    username, server_name = yield db.server_info(server_id)
    
    @inlineCallbacks
    def create_server_cb (ip, ctx_id, res_disk) :
        ip, prefix = ip.split('/', 1)
        ctx_id = str(ctx_id)
        lv_size = "%dM" % res_disk

        try :
            exit_code, output = yield backend.invoke("create", 
                "%s_%d" % (username, server_id),        # srv_name
                ctx_id,                                 # context_id
                settings.net_dev,                       # net_dev
                ip,                                     # ip
                prefix,                                 # prefix
                lv_size,                                # lv_size
            )
        except backend.BackendError, e :
            yield log.api_log(ctx, "init.create:err", (e.exitStatus, e.output))

            raise errors.InitServer_Backend()
            
        yield log.api_log(ctx, "init.create:ok", output)

    yield db.initialize_server(server_id, create_server_cb)

    returnValue( True )

@inlineCallbacks
def xmlrpc_server_status (ctx, server_id) :

    returnValue( (is_mounted, is_running, uptime_desc, load_avg_desc) )

@inlineCallbacks
def xmlrpc_mount_server (ctx, server_id) :

    returnValue( True )

@inlineCallbacks
def xmlrc_update_server_version (ctx, server_id) :

    returnValue( True )

@inlineCallbacks
def xmlrpc_start_server (ctx, server_id) :

    returnValue( True )

@inlineCallbacks
def xmlrpc_stop_server (ctx, server_id) :

    returnValue( True )

@inlineCallbacks
def xmlrpc_destroy_server (ctx, version_id) :

    returnValue( True )

