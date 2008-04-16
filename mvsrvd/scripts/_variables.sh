MODE="dev"

VSERVER_GLOBAL_DIR=/etc/vservers/
MYOTTD_DIR="/home/myottd/${MODE}"

MYOTTD_SHARED_GFX_DIR="$MYOTTD_DIR/shared_gfx"
MYOTTD_OPENTTD_DIR="$MYOTTD_DIR/openttd"
MYOTTD_SERVERS_DIR="$MYOTTD_DIR/mode-vserver/servers"

MYOTTD_FS_BASE_PATH="$MYOTTD_OPENTTD_DIR/fs_base"

srv_path="${MYOTTD_SERVERS_DIR}/${srv_name}"

vg_name="myottd_${MODE}"
lv_name="srv_${srv_name}_data"
lv_path="/dev/${vg_name}/${lv_name}"


fmt_srv_name="^[a-z][a-z0-9-]+_[0-9]+\$"
fmt_numeric="^[0-9]+\$"
fmt_if_dev="^[a-z]+[a-z0-9_]+\$"
fmt_if_ip="^([0-9]{1,3}\.){3}[0-9]{1,3}\$"
fmt_lv_size="^[0-9_]+[M]\$"
fmt_ottd_ver="^r?[0-9]+(-[a-z]+[0-9]+)?\$"

