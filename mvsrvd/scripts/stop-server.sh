#!/bin/sh

    srv_name="$1"

SCRIPT_PATH=/home/terom/myottd-dev/mvsrvd/scripts
. $SCRIPT_PATH/_variables.sh
. $SCRIPT_PATH/_functions.sh

#                       arg_name
required_argument       srv_name            "$fmt_srv_name"

using_dir "$srv_path"
    #                   name
    vserver_stop        "$srv_name"
leave_dir

