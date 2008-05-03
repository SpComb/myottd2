
from lib.api import fault


Common_NoSuchServer         = fault(3001,   "vservers.no_such_server",                  "No such server"            )

InitServer_NoMoreSlots      = fault(3011,   "vservers.initialize_server.no_more_slots", "All server slots in use"   )
InitServer_Backend          = fault(3012,   "vservers.initialize_server.backend",       "Backend error"             )

