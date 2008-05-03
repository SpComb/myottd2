from twisted.internet.defer import returnValue, inlineCallbacks, maybeDeferred

import pickle, psycopg2

class Logger (object) :
    def __init__ (self, daemon, db) :
        self.daemon = daemon
        self.db = db
    
    def _serialize (self, value) :
        return psycopg2.Binary(pickle.dumps(value, 2))
    
    @inlineCallbacks
    def api_audit (self, ctx, *args) :
        """
            Add an entry to the API audit log. 

            Deferred, records the audit id in the given ctx
        """

        ctx.audit_id = yield self.db.insertForID("""
            INSERT INTO api_audit (
                daemon, method, client, ts,    auth, arguments
            ) VALUES (
                %s,     %s,     %s,     now(), %s,     %s
            )
            """, self.daemon, ctx.method, ctx.client, ctx.auth_info, self._serialize(args)
        )
    
    def api_log (self, ctx, name, data, optionalAuditID=False) :
        """
            Add an entry to the API log.

            Deferred
        """

        assert optionalAuditID or ctx.audit_id

        return self.db.execute("""
            INSERT INTO api_log (
                audit_id, name, data
            ) VALUES (
                %s,       %s,   %s
            )
            """, getattr(ctx, 'audit_id', None), name, self._serialize(data)
        )


DEBUG = 0x01
INFO = 0x02
WARNING = 0x03
ERROR = 0x04
FATAL = 0x05

def log (level, msg, *args) :
    if args :
        msg = msg % args
    
    print msg

def _levelFunc (level) :
    def _wrapper (msg, *args) :
        return log(level, msg, *args)

    return _wrapper

debug = _levelFunc(DEBUG)
info = _levelFunc(INFO)
warning = _levelFunc(WARNING)
error = _levelFunc(ERROR)
fatal = _levelFunc(FATAL)

