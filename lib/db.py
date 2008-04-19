from twisted.enterprise import adbpi

class DB (adbapi.ConnectionPool) :
    def __init__ (self, db_config, db_password) :
        adbapi.ConnectionPool.__init__("pgdb",
            cp_min      = 1,
            cp_max      = 5,

            host        = config_ns.db_host,
            database    = config_ns.db_database,
            user        = config_ns.db_user,
            password    = db_password,
        )

    def query (self, sql, *args) :
        return self.runQuery(sql, args)

    def execute (self, sql, *args) :
        return self.runOperation(sql, arg)

