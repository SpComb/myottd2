#!/bin/sh

SCRIPT_PATH=/home/terom/myottd-dev/mvsrvd/scripts
. $SCRIPT_PATH/_variables.sh
. $SCRIPT_PATH/_functions.sh

using_dir "$srv_path"
    #                   name
    vserver_stop        "$srv_name"

    #                   mountpoint                                  type
    clear_mount         "${srv_path}/guest_data/root/mnt"           "fuse"
    clear_mount         "${srv_path}/guest_data"                    "ext3"
leave_dir

