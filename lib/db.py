from twisted.enterprise import adbapi
from twisted.internet import reactor, threads

class DB (adbapi.ConnectionPool) :
    def __init__ (self, config_ns, db_password) :
        adbapi.ConnectionPool.__init__(self, "pgdb",
            cp_min      = 1,
            cp_max      = 5,

            host        = config_ns.db_host,
            database    = config_ns.db_database,
            user        = config_ns.db_user,
            password    = db_password,
        )

    def query (self, sql, *args) :
        return self.runQuery(sql, args)
    
    def _query (self, trans, sql, *args) :
        trans.execute(sql, args)

        return trans.fetchall()

    def execute (self, sql, *args) :
        return self.runOperation(sql, args)

    def _execute (self, trans, sql, *args) :
        trans.execute(sql, args)

        return None
    
    def insertForID (self, sql, *args) :
        """
            Executes the given SQL query in a deferred that callbacks with the value of psql's lastval()
        """

        return self.runInteraction(self._insertForID, sql, *args)

    def _insertForID (self, trans, sql, *args) :
        trans.execute(sql, args)
        trans.execute("SELECT lastval()")

        return trans.fetchall()[0][0]

    def modifyForRowcount (self, sql, *args) :
        """
            Executes the given SQL query in a deferred that callbacks with the number of rows affected
        """

        return self.runInteraction(self._modifyForRowcount, sql, *args)

    def _modifyForRowcount (self, trans, sql, *args) :
        trans.execute(sql, args)

        return trans.rowcount
    
    def queryOne (self, sql, *args) :
        """
            Executes the given SQL query in a deferred that callbacks with a single row as a result (or None)
        """

        return self.runInteraction(self._query, sql, *args).addCallback(self._queryOne_result)
    
    def _queryOne (self, trans, sql, *args) :
        
        return self._queryOne_result(self._query(trans, sql, *args))

    def _queryOne_result (self, result) :
        if not result :
            return None

        elif len(result) == 1 :
            return result[0]

        else :
            raise ValueError("query returned more than one row (%d)" % len(result))
    
    def runWithTransaction (self, functions) :
        """
            Used to execute a complex transaction (using the function is hence complex)

            The functions argument is a sequence of (func, args, kwargs) tuples. The function is
            executed inside the adbapi thread, and called with the same arguments as runInteraction
            uses.
            
            If you want to run a function in userland, use DB.userFunc
        """

        return self.runInteraction(self._runWithTransaction, functions)

    def _runWithTransaction (self, trans, functions) :
        ret = []

        for func, args, kwargs in functions :
            ret.append(func(trans, *args, **kwargs))

        return ret
    
    def wrapUserFunc (self, func) :
        """
            Wrap the given function such that it will be run in the reactor thread (MUST return a
            callback), and the result of that is returned.

            Meant for use with runWithTransaction
        """

        def _wrapper (trans, *args, **kwargs) :
            return threads.blockingCallFromThread(reactor, func, *args, **kwargs)

        return _wrapper
            
