from twisted.internet import reactor

import settings
import api as api_module

from secrets import api_auth as auth_db
from lib import api

def main () :
    server = api.APIServer(api_module, settings, auth_db, api_module.log)

    reactor.run()

if __name__ == '__main__' :
    main()

