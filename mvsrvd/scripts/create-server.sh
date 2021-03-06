#!/bin/sh

    srv_name="$1"
  context_id="$2"
     net_dev="$3"
      net_ip="$4"
  net_prefix="$5"
     lv_size="$6"

SCRIPT_PATH=/home/terom/myottd-dev/mvsrvd/scripts
. $SCRIPT_PATH/_variables.sh
. $SCRIPT_PATH/_functions.sh

#                       arg_name
required_argument       srv_name            "$fmt_srv_name"
required_argument       context_id          "$fmt_numeric"
required_argument       net_dev             "$fmt_if_dev"
required_argument       net_ip              "$fmt_if_ip"
required_argument       net_prefix          "$fmt_numeric"
required_argument       lv_size             "$fmt_lv_size"

using_dir "$srv_path"
    #           vg_name     lv_name     hd_size     mnt_point
    create_lv   "$vg_name"  "$lv_name"  "$lv_size"  guest_data

    using_dir guest_data
        using_dir data_rw
            using_dir ottd
                #               name                        mode
                create_dir      save                        0755
            leave_dir
        leave_dir

        using_dir root
            #               target              name
            create_sym      mnt/root/etc        etc
            create_sym      mnt/root/lib        lib
            create_sym      mnt/root/lib64      lib64
            create_sym      mnt/root/usr        usr
            create_sym      mnt/root/sbin       sbin
            create_sym      mnt/ottd            ottd

            #               name                mode
            create_fifo     console-in          0777
            create_fifo     console-out         0777

            #               name                        mode
            create_dir      mnt                         0755

            #               name
            set_barrier     ..


            using_dir dev
                #               name        major   minor   mode
                create_dev      null        1       3       0666
                create_dev      zero        1       5       0666
                create_dev      full        1       7       0666
                create_dev      random      1       8       0644
                create_dev      urandom     1       9       0644
                create_dev      tty         5       0       0666
                create_dev      ptmx        5       2       0666
                
                #               name                        mode
                create_dir      pts                         0755
            leave_dir
        leave_dir
    leave_dir

    using_dir config
        #               target                          name
        create_sym      "${srv_path}/guest_data/root"   vdir
        create_sym      "${srv_path}/lockfile"          run
        create_sym      "${srv_path}/cache"             cache

        #               name                content
        create_file     context             "$context_id"
        create_file     name                "$srv_name"

        using_dir apps
            using_dir init
                create_file     style       "plain"
            leave_dir
        leave_dir

        using_dir interfaces
            using_dir 0
                #               name                content
                create_file     dev                 "$net_dev"
                create_file     ip                  "$net_ip"
                create_file     prefix              "$net_prefix"
            leave_dir
        leave_dir
    leave_dir
leave_dir

using_dir "$VSERVER_GLOBAL_DIR"
    #               target              name
    create_sym      "$srv_path/config"  "$srv_name"
leave_dir

echo "Done"
