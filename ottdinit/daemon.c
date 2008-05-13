
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

#include <event.h>

// paths to the fifos
#define READ_FIFO_PATH  "./daemon-in"
#define WRITE_FIFO_PATH "./daemon-out"

// maximum length of a message's data
#define MAX_DATA_LEN 255

// header size in bytes
#define HEADER_SIZE 2

// the message format for the fifo data

#pragma pack(push)
#pragma pack(1)

typedef struct msg {
    unsigned char cmd;
    unsigned char len;

    char data[MAX_DATA_LEN];
} msg_t;

#pragma pack(pop)

#define PROTOCOL_VERSION 0x01

// message command codes
enum {
    CMD_INOUT_HELLO         = 0x01,
    CMD_OUT_ERROR           = 0x02,

    CMD_OUT_DATA_STDOUT     = 0x10,
    CMD_OUT_DATA_STDERR     = 0x11,

    CMD_OUT_STATUS_OK       = 0x20,
    CMD_OUT_STATUS_EXIT     = 0x21,
    CMD_OUT_STATUS_FATALITY = 0x22,
    CMD_OUT_STATUS_IDLE     = 0x2F,

    CMD_IN_DATA_STDIN       = 0x60,

    CMD_IN_DO_START         = 0x70,
    CMD_IN_DO_KILL          = 0x71,

    CMD_IN_QUERY_STATUS     = 0x80,

    CMD_MAX                 = 0xFF,
};

// error codes
enum {
    ERROR_INVALID_STATE     = 0x0001,
    ERROR_INVALID_CMD       = 0x0002,
    ERROR_INVALID_CMD_STATE = 0x0003,
    ERROR_SHORT_CMD_DATA    = 0x0004,

    ERROR_CMD_HELLO_VERSION_SIZE        = 0x0101
};

// possible states
enum {
    STATE_HELLO,
    STATE_RECOVER,
};

static int _state;

// the prototype for command handler callback functions
typedef void (*cmd_func_t) (msg_t *msg);

// the struct used to store the command handlers for each command
struct cmd_handler {
    unsigned char cmd;

    size_t min_len;

    // a function for each state
    cmd_func_t st_hello;
};

// forward declerations of the state functions
void    st_hello_enter ();
void    st_hello_cmd_hello (msg_t *msg);
void    st_recover_enter ();

// table of command handlers, indexed by cmd
static struct cmd_handler _cmd_table[CMD_MAX];

// set up the cmd_handler struct for the given cmd in the _cmd_table
void _cmd_def (int cmd, size_t min_len, cmd_func_t st_hello) {
    assert(min_len >= 0 && min_len <= MAX_DATA_LEN);

    _cmd_table[cmd].cmd = cmd;
    _cmd_table[cmd].min_len = min_len;
    _cmd_table[cmd].st_hello = st_hello;
}

// do the work needed to initialize the _cmd_table
void cmd_table_init () {
    memset(_cmd_table, 0, sizeof(_cmd_table));

    #define CMD _cmd_def
    
    //      cmd                     min_len     st_hello
    CMD(    CMD_INOUT_HELLO,        1,          st_hello_cmd_hello  );
}

// some file descriptors/event structs
static int read_fifo_fd, write_fifo_fd;

static struct event read_fifo_ev;
static struct bufferevent *write_fifo_bev;

/* perror + exit */
void die (char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

void _debug (char const *file, int line, char const *func, char const *fmt, ...) {
    va_list vargs;

    va_start(vargs, fmt);

    printf("%15s:%d %25s    ", file, line, func);
    vprintf(fmt, vargs);
    printf("\n");
}

#define DEBUG(...) _debug(__FILE__, __LINE__, __func__, __VA_ARGS__)

void protocol_error (short code) {
    DEBUG("code=0x%04X", code);
}

#define ERROR_IF(code, condition) do { if (condition) { protocol_error(code); return; } } while (0)

/* event handlers */

/*
 * Handles a message by calling the appropriate command handler
 */
void _message_handler (msg_t *msg) {
    struct cmd_handler cmd_handler = _cmd_table[msg->cmd];

    DEBUG("cmd=%d, len=%d, _state=%d", msg->cmd, msg->len, _state);
    
    // valid cmd?
    if (!cmd_handler.cmd)
        return protocol_error(ERROR_INVALID_CMD);

    if (msg->len < cmd_handler.min_len)
        protocol_error(ERROR_SHORT_CMD_DATA);

    // fetch the cmd func
    cmd_func_t func = NULL;

    switch (_state) {
        case STATE_HELLO:
            func = cmd_handler.st_hello;

            break;
    };

    DEBUG("func=%p", func);
    
    // complain about bad state re the cmd, or call the cmd
    if (!func)
        protocol_error(ERROR_INVALID_CMD_STATE);
    else
        func(msg);
}

/*
 * The handler for read events on the read_fifo fd. Reads in messages and handles them
 */
void read_fifo_handler (int fd, short event, void *arg) {
    static int read_offset = 0, read_remaining = HEADER_SIZE;
    static msg_t msg;

    ssize_t bytes_read;

    DEBUG("fd=%d, event=%d, arg=%p", fd, event, arg);
    
    while (read_remaining) {
        bytes_read = read(fd, ( (void *) &msg ) + read_offset, read_remaining);

        DEBUG("offset=%d, remaining=%d, read=%d", read_offset, read_remaining, bytes_read);
        
        if (bytes_read == -1) {
            if (errno == EAGAIN) {
                DEBUG("no more data");
                break;
            } else
                die("read(read_fifo");
        } else if (bytes_read == 0) {
            /* manager disconnected ! */
            DEBUG("EOF");

            // discard any partially read messages
            read_offset = 0;
            read_remaining = HEADER_SIZE;
            
            st_recover_enter();

            break;
        } else {
            read_offset += bytes_read;
            read_remaining -= bytes_read;
        }
        
        if (read_offset == HEADER_SIZE && read_remaining == 0) {
            // we read in the header
            read_remaining = msg.len;
        }
        
        if (read_remaining == 0) {
            // read in the full message
            _message_handler(&msg);

            // reset the read state
            read_offset = 0;
            read_remaining = HEADER_SIZE;
        }
    }
    
    if (event_add(&read_fifo_ev, NULL))
        die("event_add(read_fifo)");
}

void write_fifo_error (struct bufferevent *bev, short what, void *arg) {
    /* !?!? */

    DEBUG("what=0x%04X", what);
}

int write_fifo_send (msg_t *msg) {
    assert(write_fifo_bev);

    DEBUG("cmd=0x%02X, len=%d", msg->cmd, msg->len);

    DEBUG("bufferevent_write(write_fifo, %d)", HEADER_SIZE + msg->len);
    if (bufferevent_write(write_fifo_bev, msg, HEADER_SIZE + msg->len))
        die("bufferevent_write(write_fifo)");
}

/* open/close functions */
void read_fifo_open () {
    // open the read fifo
    DEBUG("open(\"%s\", O_RDONLY | O_NONBLOCK)", READ_FIFO_PATH);
    read_fifo_fd = open(READ_FIFO_PATH, O_RDONLY | O_NONBLOCK);

    if (read_fifo_fd == -1)
        die("open(read_fifo)");
    
    // wait for the write end to be opened and a message to be sent
    DEBUG("event_set(read_fifo, EV_READ, read_fifo_handler)");
    event_set(&read_fifo_ev, read_fifo_fd, EV_READ, read_fifo_handler, NULL);
    DEBUG("event_add(read_fifo)");

    if (event_add(&read_fifo_ev, NULL))
        die("event_add(read_fifo_ev)");
}

void read_fifo_reopen () {
    if (read_fifo_fd) {
        DEBUG("close(read_fifo)");

        if (close(read_fifo_fd))
            die("close(read_fifo)");

        read_fifo_fd = 0;
    }

    read_fifo_open();
}

void write_fifo_open () {
    // open the write fifo
    DEBUG("open(\"%s\", O_WRONLY | O_NONBLOCK)", WRITE_FIFO_PATH);
    write_fifo_fd = open(WRITE_FIFO_PATH, O_WRONLY | O_NONBLOCK);

    if (write_fifo_fd == -1)
        die("open(write_fifo)");
    
    // set up the write bufferevent
    write_fifo_bev = bufferevent_new(write_fifo_fd, NULL, NULL, write_fifo_error, NULL);

    if (write_fifo_bev == NULL)
        die("bufferevent_new(write_fifo)");
    
    // and we can enable it already
    if (bufferevent_enable(write_fifo_bev, EV_WRITE))
        die("bufferevent_enable(write_fifo)");
}

void st_hello_enter () {
    // we wait for the manager to take inital contact with us
    _state = STATE_HELLO;
    
    // open the fifo and wait for the manager to take contact
    read_fifo_open();
}

void st_recover_enter () {
    // we wait for the manager to contact us again.
    _state = STATE_RECOVER;

    // reopen the fifo and wait for the manager to take contact
    read_fifo_reopen();
}

void st_hello_cmd_hello (msg_t *msg) {
    ERROR_IF(ERROR_CMD_HELLO_VERSION_SIZE, msg->len != 1);

    unsigned char version = msg->data[0];

    // the manager has sent us the hello message
    DEBUG("version=0x%02X", version);

    // now we should be able to open the write as well
    DEBUG("open write fifo to manager");
    write_fifo_open();

    // and send the message!
    msg_t reply;

    reply.cmd = CMD_INOUT_HELLO;
    reply.len = 1;
    reply.data[0] = PROTOCOL_VERSION;

    DEBUG(" -> version=0x%02X", PROTOCOL_VERSION);

    write_fifo_send(&reply);
}

int main () {
    /*
     * The application goes through these states:
     *
     * hello:
     *  Wait for the manager to take contact to us, and greet them
     *
     * idle:
     *  Wait for the manager to tell us to launch OpenTTD, whereupon we enter the "running" state
     *
     * running:
     *  The OpenTTD child process is running. Relay stdin/out/err
     *
     * recover:
     *  If we are in the "idle" or "running" states and loose contact to the manager, we need to buffer
     *  data from OpenTTD, and wait for the manager to contact us again. In other words, this is similar to
     *  init, except we have a running OpenTTD process.
     *
     */
    
    // initialize
    cmd_table_init();
    event_init();

    // enter init phase
    st_hello_enter();
    
    // run the event dispatcher until completion.
    DEBUG("event_dispatch() ...");
    int err = event_dispatch();

    // inspect the error code... WTF is it?
    DEBUG("event_dispatch -> err=%d", err);
    
    return 0;
}
