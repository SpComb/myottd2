#!/bin/sh

    srv_name="$1"
 srv_version="$2"

SCRIPT_PATH=/home/terom/myottd-dev/mvsrvd/scripts
. $SCRIPT_PATH/_variables.sh
. $SCRIPT_PATH/_functions.sh


#                       arg_name
required_argument       srv_name            "$fmt_srv_name"
required_argument       srv_version         "$fmt_ottd_ver"

using_dir "$srv_path"
    #                   dev         mountpoint                      type
    ensure_mounted      "$lv_path"  "${srv_path}/guest_data"        "ext3"

    mount_union         "${srv_path}/guest_data/root/mnt"   \
        "guest_data/data_rw=rw"                               \
        "$MYOTTD_SHARED_GFX_DIR=ro"                           \
        "$MYOTTD_OPENTTD_DIR/fs_${srv_version}=ro"            \
        "$MYOTTD_FS_BASE_PATH=ro"
    
    #                   name
    vserver_start       "$srv_name"
leave_dir

