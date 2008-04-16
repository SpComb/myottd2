function error {
    msg="$1"

    echo "FATAL: $msg" 1>&2
    exit 1
}

function using_dir {
    name="$1"

    
    if [ ! -d "$name" ]; then
        echo "Create dir '$name'..."
        /bin/mkdir "$name" || error "mkdir($name)"
    fi;
    
    echo "Entering dir '$name'..."
    pushd "$name" > /dev/null || error "pushd($name)"
}

function leave_dir {
    echo "Leaving dir..."

    popd > /dev/null || error "popd()"
}

function create_sym {
    target="$1"
    name="$2"

    echo "Create symlink $name -> $target" 

    ln -s "$target" "$name" || error "ln($target, $name)"
}

function create_fifo {
    name="$1"
    mode="$2"

    echo "Create fifo $name ($mode)"

    /usr/bin/mkfifo "$name" --mode="$mode" || error "mkfifo($name, $mode)"
}

function create_dev {
    name="$1"
    major="$2"
    minor="$3"
    mode="$4"

    echo "Create device $name as $major.$minor ($mode)"

    /bin/mknod "$name" c "$major" "$minor" --mode="$mode" || error "mknod($name, $major, $minor, $mode)"
}

function create_dir {
    name="$1"
    mode="$2"

    echo "Create dir $name ($mode)"

    /bin/mkdir "$name" --mode="$mode" || error "mkdir($name, $mode)"
}

function create_file {
    name="$1"
    data="$2"

    echo "Create file $name with contents: $data"

    /bin/echo "$data" > "$name" || error "echo($name, $data)"
}

function set_barrier {
    dir="$1"

    echo "Set --barrier attribute on '$dir'"

    /usr/sbin/setattr --barrier "$dir" || error "setattr_barrier($dir)"
}

function create_lv {
    vg_name="$1"
    lv_name="$2"
    lv_size="$3"
    mnt_point="$4"

    echo "Create an LV called /dev/${vg_name}/${lv_name} of size $lv_size and mount on $mnt_point"

    /sbin/lvcreate --size="$lv_size" --name="$lv_name" "$vg_name" || error "lvcreate($vg_name, $lv_name, $lv_size)"
    /sbin/mkfs.ext3 /dev/${vg_name}/${lv_name} || error "mkfs.ext3($vg_name, $lv_name)"
    /bin/mkdir $mnt_point || error "mkdir($mnt_point)"
    /bin/mount /dev/${vg_name}/${lv_name} $mnt_point || error "mount($vg_name, $lv_name, $mnt_point)"
}

function remove_lv {
    vg_name="$1"
    lv_name="$2"

    echo "Remove an LV called /dev/${vg_name}/${lv_name}"
    
    /sbin/lvremove -- "${vg_name}/${lv_name}" || error "lvremove($vg_name, $lv_name)"
}

function remove_dir {
    path="$1"

    echo "Remove dir at '$path'..."

    /bin/rm --verbose --recursive --interactive=once -- "$path" || error "rm_recursive($path)"
}

function remove_sym {
    path="$1"

    if [ ! -h "$path" ]; then
        error "$path is not a symlink!"
    fi

    echo "Remove symlink at '$path'..."
    /bin/rm --verbose -- "$path" || error "rm($path)"
}

function mount_union {
    mount_point="$1"
    dirs=""

    clear_mount "$mount_point" "fuse"
    
    shift; 

    echo "Mounting unionfs on '$mount_point':"

    for branch in $*; do
        if [ -z "$dirs" ]; then
            dirs="$branch"
        else
            dirs="$branch:$dirs"
        fi

        echo "$branch"
    done;

    /usr/bin/funionfs -o allow_other,dirs=$dirs none $mount_point || error "funionfs($dirs, $mount_point)"
}

function vserver_start {
    srv_name="$1"

    echo "Starting vserver '$srv_name'..."

    /usr/sbin/vserver "$srv_name" start || error "vserver_start($srv_name)"
}

function vserver_stop {
    srv_name="$1"

    echo "Stopping vserver '$srv_name'..."

    /usr/sbin/vserver "$srv_name" stop || error "vserver_stop($srv_name)"
}

function is_mounted {
    suffix="$1"
    type="$2"

    echo -n "Checking if '...$suffix' ($type) is mounted... "

    if [ "`/bin/mount | /bin/grep "$suffix type $type" -c`" -gt 0 ]; then
        echo "Yes"
        true
    else
        echo "No"
        false
    fi
}

function clear_mount {
    path="$1"
    type="$2"

    if is_mounted "$path" "$type"; then
        echo "Unmounting..."
        /bin/umount "$path" || error "umount($path)"
    fi
}

function ensure_mounted {
    dev="$1"
    path="$2"
    type="$3"
    
    if ! is_mounted "$path" "$type"; then
        echo "Mounting..."
        /bin/mount "$dev" "$path"
    fi;
}

