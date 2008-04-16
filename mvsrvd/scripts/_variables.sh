MODE="dev"

VSERVER_GLOBAL_DIR=/etc/vservers/
MYOTTD_DIR="/home/myottd/${MODE}"

MYOTTD_SHARED_GFX_DIR="$MYOTTD_DIR/shared_gfx"
MYOTTD_OPENTTD_DIR="$MYOTTD_DIR/openttd"
MYOTTD_SERVERS_DIR="$MYOTTD_DIR/mode-vserver/servers"

MYOTTD_FS_BASE_PATH="$MYOTTD_OPENTTD_DIR/fs_base"

srv_name="test3"
srv_version="060"

context_id=20002

net_dev="dummy0"
net_ip="10.22.11.3"
net_prefix="24"


srv_path="${MYOTTD_SERVERS_DIR}/${srv_name}"

vg_name="myottd_${MODE}"
lv_name="srv_${srv_name}_data"
lv_size="20M"
lv_path="/dev/${vg_name}/${lv_name}"

