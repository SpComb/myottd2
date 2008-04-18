#!/bin/sh

vg_name="$1"
lv_name="$2"
hdd_size_spec="$3"

/sbin/lvcreate --size="$hdd_size_spec" --name="$lv_name" "$vg_name"
/sbin/mkfs.ext3 /dev/${vg_name}/${lv_name}

