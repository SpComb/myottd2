
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

// paths to the fifos
#define FIFO_IN_PATH  "/daemon-in"
#define FIFO_OUT_PATH "/daemon-out"

// maximum length of a message's data
#define MAX_MSG_LEN 255


// the message format for the fifo data
struct msg {
    unsigned char cmd;
    unsigned char len;

    char data[MAX_MSG_LEN];
}

// message command codes
enum {
    CMD_OUT_DATA_STDOUT     = 0x10,
    CMD_OUT_DATA_STDERR     = 0x11,

    CMD_OUT_STATUS_OK       = 0x20,
    CMD_OUT_STATUS_EXIT     = 0x21,
    CMD_OUT_STATUS_FATALITY = 0x22,
    CMD_OUT_STATUS_IDLE     = 0x2F,

    CMD_IN_DATA_STDIN       = 0x60,

    CMD_IN_DO_START         = 0x70,
    CMD_IN_DO_KILL          = 0x71,

    CMD_IN_QUERY_STATUS     = 0x80
};

// the fds for the in/out fifos
static int fifo_in_fd, fifo_out_fd;

/* perror + exit */
void die (char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

int send_message (unsigned char cmd, size_t len, char *data) {
    struct msg msg_buf;
    size_t written;
    
    // don't truncate, drop
    if (len > MAX_MSG_LEN) {
        fprintf(stderr, "WARNING: Oversized message of %d bytes dropped: %x %s\n", len, cmd, data);
        return 1;
    }
    
    // copy over directly
    msg_buf.cmd = cmd;
    msg_buf.len = len;
    
    // if len == 0, we don't need to send any data
    if (len) {
        assert(data != NULL);

        memcpy(&msg_buf.data, data, len);
    }
    
    // write the message to the out fifo
    written = write(fifo_out_fd, &msg_buf, 2 + len);
    
    // since these writes are only 257 bytes at most, they should fit in atomically
    assert(written == 2 + len);
    
    // success
    return 0;
}

int open_fifos () {
    // first open the write fifo in blocking mode, and then open the read fifo in blocking mode
    
    // write fifo...
    if ((fifo_out_fd = open(FIFO_OUT_PATH, O_CLOEXEC | O_SYNC, O_WRONLY)) == -1) die("open(FIFO_OUT_PATH)");

    // read fifo
    if ((fifo_in_fd = open(FIFO_IN_PATH, C_CLOEXEC, O_RDONLY)) == -1) die("open(FIFO_IN_PATH)");
    
    // send a hello message
    send_message(CMD_OUT_STATUS_IDLE, 0, NULL);

    return 0;
}

int main_loop () {
    // the message buffer that we read messages into
    struct msg recv_buf;

    // how many bytes we've read
    size_t recv_pos = 0;

    int running = 1;

    while (running) {
        
    }
}

int main () {
    open_fifos();
    
    main_loop();

    return 0;
}
