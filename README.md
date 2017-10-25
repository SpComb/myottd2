# [Archive] myottd2 (2008)

***Archived for historical curiosity***, this is the WIP reimplementation of myottd.net with a containerzed microservice architecture.

See the [TT-Forums thread from 2007](https://www.tt-forums.net/viewtopic.php?t=34194) for more historical context.

See the [myottd](https://github.com/SpComb/myottd) repo for the original monolithic prototype that was actually running in "production" from 2007-2008.

## Design Docs

* [General philosophy](design.txt)
* [`msrvd`](mvsrvd/design.txt) vserver management service
* [`ottdinit`](ottdinit/design.txt) vserver init+daemon/service manager with remote control
* [database schema](myottd-database.txt)
* [XML-RPC API](myottd-xmlrpc-api.txt)

## Further Work

* [`netdaemon`](https://github.com/SpComb/netdaemon) improved container init + daemon/service manager implementation
