from lib import buffer

import os, select

def main (read_fifo_path, write_fifo_path) :
    write_fh = open(write_fifo_path, "w", 0);

    read_fd = os.open(read_fifo_path, os.O_RDONLY | os.O_NONBLOCK)

    buf = buffer.WriteBuffer()

    buf.writeStruct("BBB", 0x01, 1, 0x0F)

    write_fh.write(buf.getvalue())

    select.select([read_fd], [], [])

    msg = os.read(read_fd, 3)

    print "got %d bytes" % len(msg)
    
    buf = buffer.ReadBuffer(msg)
    cmd, len_, version = buf.readStruct("BBB")

    print "0x%02X %d = 0x%02X" % (cmd, len_, version)

    os.close(read_fd)
    write_fh.close()

if __name__ == '__main__' :
    main("test/daemon-out", "test/daemon-in")

