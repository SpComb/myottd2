from twisted.enterprise import adbapi
from twisted.internet import reactor, threads

def callFromTransaction (func, *args, **kwargs) :
    return threads.blockingCallFromThread(reactor, func, *args, **kwargs)

class DB (adbapi.ConnectionPool) :
    def __init__ (self, config_ns, db_password) :
        adbapi.ConnectionPool.__init__(self, "psycopg2",
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
    
    def runAsTransaction (self, function, *args, **kwargs) :
        """
            Used to execute a transaction
        """

        return self.runInteraction(function, *args, **kwargs)

    def wrapAsTransaction (self, func) :
        """
            Meant to be used as a decorator, calls the given function as a transaction
        """

        def _wrapper (*args) :
            return self.runAsTransaction(func, *args)

        return _wrapper


