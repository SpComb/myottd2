from twisted.internet.defer import returnValue, inlineCallbacks

from lib import utils, api, log
import db, backend, settings, errors

from lib import log as _log

log = _log.Logger("vserver", db.db)

# a simplistic solution to the server-mounting issue
_server_mounted = dict()

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
            yield log.api_log(ctx, "init.backend:err", (e.exitStatus, e.output))

            raise errors.InitServer_Backend()
            
        yield log.api_log(ctx, "init.backend:ok", output)

    yield db.initialize_server(server_id, create_server_cb)

    returnValue( True )

@inlineCallbacks
def xmlrpc_server_state (ctx, server_id) :
    """
       Is the given server running or not? 
    """

    context_id, = yield db.server_context_id(server_id)
    
    is_running = backend.server_state(context_id)

    # no need to audit-log
    ctx.dontLogResult()

    returnValue( is_running )

@inlineCallbacks
def xmlrpc_mount_server (ctx, server_id) :
    """
        Mounts the filesystem for the given server ID with the server's OpenTTD version (from the database), but doesn't
        start it. If the filesystem is already mounted (irregardless of the OpenTTD version), this is a no-op.

        The is-already-mounted check is done without invoking the backend - the backend is only invoked if we come to
        the conclusion that the server is not mounted. The detection mechanism probably isn't 100% reliable - there
        needs to be some fallback in case this fails.
    """

    # simplistic method
    if server_id in _server_mounted :
        # no need to audit-log
        ctx.dontLogResult()

        returnValue( True )

    yield log.api_audit(ctx, server_id)

    username, server_name, server_version, server_port = yield db.server_details(server_id)
    
    try :
        exit_code, output = yield backend.invoke("mount",
            "%s_%d" % (username, server_id),        # srv_name
            server_version,
        )
    except backend.BackendError, e :
        yield log.api_log(ctx, "mount.backend:err", (e.exitStatus, e.output))

        raise errors.InitServer_Backend()
        
    yield log.api_log(ctx, "mount.backend:ok", output)
    
    # mark the server as mounted
    _server_mounted[server_id] = True

    returnValue( True )

@inlineCallbacks
def xmlrc_update_server_version (ctx, server_id) :
    """
        Force-remount the vserver's filesystem to change it to a new version of OpenTTD.

        Very similar to mount_server
    """
 
    yield log.api_audit(ctx, server_id)

    username, server_name, server_version, server_port = yield db.server_details(server_id)
    
    try :
        exit_code, output = yield backend.invoke("mount",
            "%s_%d" % (username, server_id),        # srv_name
            server_version,
        )
    except backend.BackendError, e :
        yield log.api_log(ctx, "mount.backend:err", (e.exitStatus, e.output))

        raise errors.InitServer_Backend()
        
    yield log.api_log(ctx, "mount.backend:ok", output)
    
    # mark the server as mounted
    _server_mounted[server_id] = True

    returnValue( True )

@inlineCallbacks
def xmlrpc_start_server (ctx, server_id) :
    """
        Starts up an already created server, (re)mounting the correct version of OpenTTD if needed.
    """

    yield log.api_audit(ctx, server_id)

    username, server_name, server_version, server_port = yield db.server_details(server_id)
    
    try :
        exit_code, output = yield backend.invoke("start",
            "%s_%d" % (username, server_id),        # srv_name
            server_version,
            str(server_port),
        )
    except backend.BackendError, e :
        yield log.api_log(ctx, "start.backend:err", (e.exitStatus, e.output))

        raise errors.InitServer_Backend()
        
    yield log.api_log(ctx, "start.backend:ok", output)

    # mark the server as mounted
    _server_mounted[server_id] = True

    returnValue( True )

@inlineCallbacks
def xmlrpc_stop_server (ctx, server_id) :
    """
        Stop a running server
    """

    yield log.api_audit(ctx, server_id)

    username, server_name = yield db.server_info(server_id)

    try :
        exit_code, output = yield backend.invoke("stop",
            "%s_%d" % (username, server_id),        # srv_name
        )
    except backend.BackendError, e :
        yield log.api_log(ctx, "stop.backend:err", (e.exitStatus, e.output))

        raise errors.InitServer_Backend()
        
    yield log.api_log(ctx, "stop.backend:ok", output)

    returnValue( True )

@inlineCallbacks
def xmlrpc_destroy_server (ctx, server_id) :

    returnValue( False )

