from twisted.internet import reactor
from twisted.internet.defer import returnValue, inlineCallbacks, maybeDeferred

from lib.db import DB

import settings
from secrets import db_password

import pickle, pprint

db = DB(settings, db_password)

def main () :

    reactor.run()

def _unserialize (blob) :
    return pickle.loads(blob)

@inlineCallbacks
def read_audit_entry (audit_id) :
    daemon, method, client, ts, auth, arguments = yield db.queryOne("""
        SELECT
            daemon, method, client, ts, auth, arguments
        FROM
            api_audit
        WHERE
            id = %s
        """, audit_id
    )

    log_events = yield db.query("""
        SELECT
            name, data
        FROM
            api_log
        WHERE
            audit_id = %s
        """, audit_id
    )

    print "Method %s.%s%r invoked by [%s:%s] at [%s], %d log entries" % (daemon, method, _unserialize(arguments), client, auth, ts, len(log_events))

    for name, data in log_events :
        print "\t%s:" % name

        pprint.pprint(_unserialize(data))
    
    reactor.stop()

@inlineCallbacks
def list_audit_entries () :
    res = yield db.query("""
        SELECT
            id, daemon, method
        FROM
            api_audit
        ORDER BY
            ts DESC
        LIMIT 10
        """
    )
    
    res.reverse()

    for id, daemon, method in res :
        print "\t%8d: %s.%s" % (id, daemon, method)

    reactor.stop()

if __name__ == '__main__' :
    from sys import argv
    
    argv.pop(0)
    
    if argv :
        audit_id = int(argv[0])

        read_audit_entry(audit_id)
    else :
        list_audit_entries()

    reactor.run()

