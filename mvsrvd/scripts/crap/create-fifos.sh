#!/bin/sh

function create_fifo {
    name="$1"
    mode="$2"

    /usr/bin/mkfifo "$name" --mode="$mode"
}

#               name        major   minor   mode
create_fifo     console-in                  0777
create_fifo     console-out                 0777

