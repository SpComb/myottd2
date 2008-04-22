from twisted.internet import reactor

import settings
import api as api_module
from secrets import api_auth as auth_db
from lib import api

def main () :
#    api.xmlrpc_check_login(None, 
#        "testusr2", "65e156e673a5aa103f0bf18762c443ce", "terom+myottd-dev-2@fixme.fi", "http://skrblz.fixme.fi/foo?uid=%(user_id)s&username=%(username)s"
#        "testusr2", "65e156e673a5aa103f0bf18762c443ce"
#        33, "87159e067c0d39f1dcf10bc0e704002c"
#    ).addBoth(gotResult)

    server = api.APIServer(api_module, settings, auth_db)

    reactor.run()

if __name__ == '__main__' :
    main()

