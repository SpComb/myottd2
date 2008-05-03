from twisted.internet.defer import returnValue, inlineCallbacks, maybeDeferred

from secrets import db_password
import settings, errors

from lib.db import DB, callFromTransaction

db = DB(settings, db_password)

@db.wrapAsTransaction
def initialize_server (trans, server_id, backend_create_cb) :
    # fetch an unused server_location for use with the new server
    res = db._queryOne(trans, """
        SELECT 
            id, ip, context 
        FROM
            v_server_locations_unused
        ORDER BY
            id ASC 
        LIMIT 1
        """
    )

    if not res :
        raise errors.InitServer_NoMoreSlots()

    loc_id, loc_ip, loc_ctx = res
    
    # update the server to use this location
    mod = db._modifyForRowcount(trans, """
        UPDATE servers SET
                location = %s
            WHERE id = %s
        """,
            loc_id, server_id
    )

    assert mod, "server went away (servers-update had zero rowcount)"
    
    # fetch the resource limit information
    res = db._queryOne(trans, """
        SELECT 
            rc.hdd_size
        FROM
            resource_classes rc INNER JOIN servers s
                ON s.res_class = rc.name
        WHERE
            s.id = %s
        """,
            server_id
    )

    assert res, "invalid res_class"

    res_disk, = res
    
    # call the given cb that does the actual backend creation
    cb_ret = callFromTransaction(backend_create_cb, loc_ip, loc_ctx, res_disk)

    # nothing to return
    return None

@inlineCallbacks
def server_info (server_id) :
    res = yield db.queryOne("""
        SELECT
            vu.username, 
            s.name 
        FROM 
            servers s LEFT JOIN v_usernames vu 
                ON s.owner = vu.id
        WHERE 
            s.id = %s
        """, 
            server_id
    )

    if not res :
        raise errors.Common_NoSuchServer()

    returnValue( res )

