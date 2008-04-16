#!/bin/sh

SCRIPT_PATH=/home/terom/myottd-dev/mvsrvd/scripts
. $SCRIPT_PATH/_variables.sh
. $SCRIPT_PATH/_functions.sh

using_dir "$srv_path"
    #                   mountpoint                                  type
    clear_mount         "${srv_path}/guest_data/root/mnt"           "fuse"
    clear_mount         "${srv_path}/guest_data"                    "ext3"

    #                   vg_name         lv_name
    remove_lv           "$vg_name"      "$lv_name"
    
    #                   path
    remove_dir          "${srv_path}"
leave_dir

using_dir "$VSERVER_GLOBAL_DIR"
    remove_sym          "$srv_name"
leave_dir

