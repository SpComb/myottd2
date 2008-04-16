#!/bin/sh

SCRIPT_PATH=/home/terom/myottd-dev/mvsrvd/scripts
. $SCRIPT_PATH/_variables.sh
. $SCRIPT_PATH/_functions.sh

using_dir "$srv_path"
    mount_union         guest_data/root/mnt         \
        guest_data/data_rw=rw                       \
        $MYOTTD_SHARED_GFX_DIR=ro                   \
        $MYOTTD_OPENTTD_DIR/fs_${srv_version}=ro    \
        $MYOTTD_FS_BASE_PATH=ro
    
    vserver_start       "$srv_name"
leave_dir

