from lib import buffer

import os, select

def main (read_fifo_path, write_fifo_path) :
    write_fh = open(write_fifo_path, "w", 0);

    read_fd = os.open(read_fifo_path, os.O_RDONLY | os.O_NONBLOCK)

    buf = buffer.WriteBuffer()

    buf.writeStruct("BBB", 0x01, 1, 0x0F)

    write_fh.write(buf.getvalue())

    buf = buffer.ReadBuffer(read(read_fd, 2))
    cmd, len_ = buf.readStruct("BB")

    data = read(read_fd, len_)

    print "0x%02X %d = %s" % (cmd, len_, buffer.hex(data))

    os.close(read_fd)
    write_fh.close()

def read (fd, bytes) :
    select.select([fd], [], [])

    msg = os.read(fd, bytes)

    print "got %d/%d bytes" % (len(msg), bytes)

    return msg
    

if __name__ == '__main__' :
    main("test/daemon-out", "test/daemon-in")

