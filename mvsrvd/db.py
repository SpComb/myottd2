
from secrets import db_password
import settings

from lib import db as _db

db = _db.DB(settings, db_password)

def server_info (server_id) :
    return db.query("SELECT s.name, s.port, ov.name FROM servers AS s LEFT JOIN ottd_versions AS ov ON s.version = ov.id WHERE s.id = %s", server_id).addCallback(_got_server_info)

def _got_server_info (res) :
    name, port, version = res[0]

    return name, port, version


