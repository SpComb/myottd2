from lib import buffer

import os, select, time

def main (read_fifo_path, write_fifo_path) :
    write_fh = open(write_fifo_path, "w", 0);

    read_fd = os.open(read_fifo_path, os.O_RDONLY | os.O_NONBLOCK)

    write_msg(write_fh, 0x01, "\x01")
    read_msg(read_fd)

    write_msg(write_fh, 0x80, "")
    read_msg(read_fd)

    write_msg(write_fh, 0x70, "\x01\x06--test")
    read_msg(read_fd)

    time.sleep(2)

    write_msg(write_fh, 0x80, "")
    read_msg(read_fd)

    write_msg(write_fh, 0x71, "\x0F")
    read_msg(read_fd)

    write_msg(write_fh, 0x80, "")
    read_msg(read_fd)

    os.close(read_fd)
    write_fh.close()

def write_msg (fh, cmd, data) :
    buf = buffer.WriteBuffer()

    buf.writeStruct("BB", cmd, len(data))
    buf.write(data)

    fh.write(buf.getvalue())

def read_msg (fd) :
    buf = buffer.ReadBuffer(read(fd, 2))
    cmd, len_ = buf.readStruct("BB")

    data = read(fd, len_)

    print "0x%02X %d = %s" % (cmd, len_, buffer.hex(data))

def read (fd, bytes) :
    select.select([fd], [], [])

    msg = os.read(fd, bytes)

    print "got %d/%d bytes" % (len(msg), bytes)

    return msg
    

if __name__ == '__main__' :
    main("test/daemon-out", "test/daemon-in")

