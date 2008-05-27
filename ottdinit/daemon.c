/*
 * A daemon that controlls a running process, providing a management/status/input/output interface via fifos
 */


#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>

#include <event.h>

#include "process.h"

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
    CMD_OUT_REPLY           = 0x03,

    CMD_OUT_DATA_STDOUT     = 0x10,
    CMD_OUT_DATA_STDERR     = 0x11,

    CMD_OUT_STATUS          = 0x20,

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

    ERROR_CMD_ARGS_SIZE             = 0xA101,

    ERROR_CMD_PROCESS_INTERNAL      = 0xA201,
    ERROR_PROCESS_NOT_RUNNING       = 0xA202,
    ERROR_PROCESS_ALREADY_RUNNING   = 0xA203,

    ERROR_CMD_START_ARGS_COUNT      = 0x7002,
};

// reply codes
enum {
    REPLY_SUCCESS           = 0x0000,   

    REPLY_HELLO             = 0x0100,
    
    REPLY_STATUS_IDLE       = 0x8000,
    REPLY_STATUS_RUN        = 0x8001,
    REPLY_STATUS_EXIT       = 0x8002,   // exit_code
    REPLY_STATUS_KILLED     = 0x8003,   // signal
    REPLY_STATUS_ERR        = 0x80FF,   // errno
};

// possible states
enum {
    STATE_HELLO     = 0x01,
    STATE_RECOVER   = 0x02,
    STATE_IDLE      = 0x04,
    STATE_RUN       = 0x08,
};

static int _state;

// the prototype for command handler callback functions
typedef void (*cmd_func_t) (msg_t *msg);

// the struct used to store the command handlers for each command
struct cmd_handler {
    unsigned char cmd;

    size_t min_len;

    int valid_states;

    cmd_func_t func;
};

// forward declerations of the state functions
int     write_fifo_send (msg_t *msg);
void    read_fifo_close ();
void    write_fifo_close ();
void    write_pipe_close ();

void    st_hello_enter ();
void    st_recover_enter ();
void    st_idle_enter ();
void    st_run_enter ();

void    cmd_hello (msg_t *msg);
void    cmd_start (msg_t *msg);
void    cmd_kill (msg_t *msg);
void    cmd_query_status (msg_t *msg);
void    cmd_data_stdin (msg_t *msg);


// table of command handlers, indexed by cmd
static struct cmd_handler _cmd_table[CMD_MAX];

// set up the cmd_handler struct for the given cmd in the _cmd_table
void _cmd_def (int cmd, size_t min_len, int valid_states, cmd_func_t func) {
    assert(min_len >= 0 && min_len <= MAX_DATA_LEN);
    
    struct cmd_handler *ch = &_cmd_table[cmd];

    ch->cmd = cmd;
    ch->min_len = min_len;
    ch->valid_states = valid_states;
    ch->func = func;
}

// do the work needed to initialize the _cmd_table
void cmd_table_init () {
    memset(_cmd_table, 0, sizeof(_cmd_table));

    #define CMD _cmd_def
    
    //      cmd                     min_len     valid_states                    func
    CMD(    CMD_INOUT_HELLO,        1,          STATE_HELLO | STATE_RECOVER,    cmd_hello           );
    CMD(    CMD_IN_DO_START,        1,          STATE_IDLE,                     cmd_start           );
    CMD(    CMD_IN_DO_KILL,         1,          STATE_RUN,                      cmd_kill            );
    CMD(    CMD_IN_QUERY_STATUS,    0,          STATE_IDLE | STATE_RUN,         cmd_query_status    );
    CMD(    CMD_IN_DATA_STDIN,      1,          STATE_RUN,                      cmd_data_stdin      );
}

// some file descriptors/event structs
static int read_fifo_fd, write_fifo_fd;

static struct event read_fifo_ev, sigchld_ev, stdout_pipe_ev, stderr_pipe_ev;
static struct bufferevent *write_fifo_bev, *write_pipe_bev;

static unsigned char _stdout_data_cmd = CMD_OUT_DATA_STDOUT, _stderr_data_cmd = CMD_OUT_DATA_STDERR;

/* debugging/logging/etc */

/*
 * perror + exit
 */
void die (char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

/*
 * fancy debug
 */
void _debug (int level, char const *file, int line, char const *func, char const *fmt, ...) {
    va_list vargs;

    if (!level)
        return;

    va_start(vargs, fmt);

    printf("%15s:%d %25s    ", file, line, func);
    vprintf(fmt, vargs);
    printf("\n");
}

#define DEBUG_FIFO_READ 0
#define DEBUG_FIFO_EOF 1
#define DEBUG_FIFO_ERROR 1
#define DEBUG_FIFO_WRITE 0
#define DEBUG_FIFO_OPEN 1
#define DEBUG_FIFO_CLOSE 1

#define DEBUG_PROTO_REPLY 1
#define DEBUG_PROTO_CMD_SEND 1
#define DEBUG_PROTO_CMD_DEBUG 0

#define DEBUG_SIGCHLD_INFO 1
#define DEBUG_SIGCHLD_DEBUG 0

#define DEBUG_PROC_STATUS 1

#define DEBUG_PIPE_READ 1
#define DEBUG_PIPE_EOF 1
#define DEBUG_PIPE_ERROR 1
#define DEBUG_PIPE_WRITE 1
#define DEBUG_PIPE_OPEN 1
#define DEBUG_PIPE_CLOSE 1

#define DEBUG_STATE 1

#define DEBUG_CMD_HELLO 1
#define DEBUG_CMD_START 1
#define DEBUG_CMD_KILL 1
#define DEBUG_CMD_STATUS 1
#define DEBUG_CMD_STDIN 1

#define DEBUG_MAIN 1

#define DEBUG(level, ...) _debug(DEBUG_##level, __FILE__, __LINE__, __func__, __VA_ARGS__)

/*
 * protocol-level error
 */
void protocol_error (uint16_t code) {
    DEBUG(PROTO_REPLY, "code=0x%04X", code);

    if (write_fifo_fd) {
        msg_t errmsg;

        errmsg.cmd = CMD_OUT_ERROR;
        errmsg.len = sizeof(uint16_t);
        *((uint16_t *) errmsg.data) = htons(code);

        write_fifo_send(&errmsg);
    }
}

void protocol_reply (uint16_t reply, uint16_t data) {
    DEBUG(PROTO_REPLY, "reply=0x%04X", reply);

    if (write_fifo_fd) {
        msg_t msg;

        msg.cmd = CMD_OUT_REPLY;
        msg.len = sizeof(reply) + sizeof(data);

        uint16_t * msg_data = (uint16_t *) msg.data;

        msg_data[0] = htons(reply);
        msg_data[1] = htons(data);

        write_fifo_send(&msg);
    }
}

void _proc_status_to_reply (const struct process_info *pinfo, short *code, short *data) {
    switch (pinfo->status) {
        case PROC_IDLE :
            DEBUG(PROC_STATUS, "PROC_IDLE");
            *code = REPLY_STATUS_IDLE, *data = 0;
            break;

        case PROC_RUN :
            DEBUG(PROC_STATUS, "PROC_RUN");
            *code = REPLY_STATUS_RUN, *data = 0;
            break;

        case PROC_EXIT :
            DEBUG(PROC_STATUS, "PROC_EXIT: %d", pinfo->exit_status);
            *code = REPLY_STATUS_EXIT, *data = pinfo->exit_status;
            break;

        case PROC_KILLED :
            DEBUG(PROC_STATUS, "PROC_KILLED: %d", pinfo->signal);
            *code = REPLY_STATUS_KILLED, *data = pinfo->signal;
            break;

        case PROC_ERR :
            DEBUG(PROC_STATUS, "PROC_ERR: %s: %s", pinfo->errmsg, strerror(pinfo->errnum));
            *code = REPLY_STATUS_ERR, *data = pinfo->errnum;
            break;

        default :
            assert(0);
    }
}


#define ERROR_IF(code, condition) do { if (condition) { protocol_error(code); return; } } while (0)

/* I/O ops */

/*
 * Handles a message by calling the appropriate command handler
 */
void _message_handler (msg_t *msg) {
    struct cmd_handler cmd_handler = _cmd_table[msg->cmd];

    DEBUG(PROTO_CMD_DEBUG, "cmd=%d, len=%d, _state=%d", msg->cmd, msg->len, _state);
    
    // valid cmd?
    if (!cmd_handler.cmd)
        return protocol_error(ERROR_INVALID_CMD);

    if (msg->len < cmd_handler.min_len)
        return protocol_error(ERROR_SHORT_CMD_DATA);
        
    if (!(cmd_handler.valid_states & _state))
        return protocol_error(ERROR_INVALID_CMD_STATE);

    DEBUG(PROTO_CMD_DEBUG, "func=%p", cmd_handler.func);
    
    // complain about bad state re the cmd, or call the cmd
    cmd_handler.func(msg);
}

/*
 * We lost the FIFO connection
 */
void handle_read_fifo_eof () {
    DEBUG(FIFO_EOF, "EOF");

    // close the write fifo so it's not dangling
    write_fifo_close();

    // and close the read fifo as it's useless now
    read_fifo_close();
    
    // what state we enter next depends on where we are now
    if (_state == STATE_IDLE || _state == STATE_HELLO) {
        // no process running
        st_hello_enter();
    } else if (_state == STATE_RUN) {
        // eek, a process running... we need to recover
        st_recover_enter();
    } else {
        // WTF?
        assert(0);
    }
}

/*
 * The handler for read events on the read_fifo fd. Reads in messages and handles them
 */
void read_fifo_handler (int fd, short event, void *arg) {
    static int read_offset = 0, read_remaining = HEADER_SIZE;
    static msg_t msg;

    ssize_t bytes_read;

    DEBUG(FIFO_READ, "fd=%d, event=%d, arg=%p", fd, event, arg);
    
    while (read_remaining) {
        bytes_read = read(fd, ( (void *) &msg ) + read_offset, read_remaining);

        DEBUG(FIFO_READ, "offset=%d, remaining=%d, read=%d", read_offset, read_remaining, bytes_read);
        
        if (bytes_read == -1) {
            if (errno == EAGAIN) {
                DEBUG(FIFO_READ, "no more data");
                break;
            } else
                die("read(read_fifo");
        } else if (bytes_read == 0) {
            /* manager disconnected ! */
            DEBUG(FIFO_READ, "EOF");

            // discard any partially read messages
            read_offset = 0;
            read_remaining = HEADER_SIZE;
            
            handle_read_fifo_eof();

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

/* SIGCHLD handler */
void sigchld_handler (int fd, short event, void *arg) {
    DEBUG(SIGCHLD_DEBUG, "SIGCHLD recieved");

    // call process_status to update the process status
    const struct process_info *pinfo = process_status();
    DEBUG(SIGCHLD_DEBUG, "process_status -> %p", pinfo);

    // close stdin
    write_pipe_close();
    
    // translate this into the protocol-level info
    short code, data;

    _proc_status_to_reply(pinfo, &code, &data);

    DEBUG(SIGCHLD_INFO, "SIGCHLD, proc_status = 0x%04X %d", code, data);
    
    // send it as a CMD_OUT_STATUS message
    msg_t msg;

    msg.cmd = CMD_OUT_STATUS;
    msg.len = 2 * sizeof(uint16_t);
    
    short *msg_data = (short *) msg.data;

    msg_data[0] = htons(code);
    msg_data[1] = htons(data);

    write_fifo_send(&msg);
    
    // and enter the correct state (the process isn't running anymore)
    
    if (_state == STATE_RUN) {
        st_idle_enter();
    } else if (_state == STATE_RECOVER) {
        st_hello_enter();
    } else {
        assert(0);
    }
}

void write_fifo_error (struct bufferevent *bev, short what, void *arg) {
    /* !?!? */

    DEBUG(FIFO_ERROR, "what=0x%04X", what);
}

int write_fifo_send (msg_t *msg) {
    assert(write_fifo_bev);

    DEBUG(PROTO_CMD_SEND, "cmd=0x%02X, len=%d", msg->cmd, msg->len);

    DEBUG(FIFO_WRITE, "bufferevent_write(write_fifo, %d)", HEADER_SIZE + msg->len);
    if (bufferevent_write(write_fifo_bev, msg, HEADER_SIZE + msg->len))
        die("bufferevent_write(write_fifo)");
}

/* data from the child process, arg is the message command to use (unsigned char *) */
void read_pipe_handler (int fd, short event, void *arg) {
    msg_t msg;
    unsigned char *msg_cmd = (unsigned char *) arg;

    msg.cmd = *msg_cmd;
    
    DEBUG(PIPE_READ, "fd=%d, event=%d, arg=%p, cmd=0x%02X", fd, event, arg, msg.cmd);

    msg.len = read(fd, msg.data, MAX_DATA_LEN);

    DEBUG(PIPE_READ, "read %d bytes", msg.len);

    write_fifo_send(&msg);

    if (msg.len) {
        switch(*msg_cmd) {
            case CMD_OUT_DATA_STDOUT :
                event_add(&stdout_pipe_ev, NULL);
                break;

            case CMD_OUT_DATA_STDERR :
                event_add(&stderr_pipe_ev, NULL);
                break;

            default :
                assert(0);
        }
    } else {
        DEBUG(PIPE_EOF, "EOF on fd %d, cmd 0x%04X", fd, *msg_cmd);

        DEBUG(PIPE_EOF, "close(%d)", fd);
        if (close(fd))
            die("close(pipe_?)");
    }
}

void write_pipe_error (struct bufferevent *bev, short what, void *arg) {
    /* !?!? */

    DEBUG(PIPE_ERROR, "what=0x%04X", what);
}

int write_pipe_send (char *data, size_t len) {
    assert(write_pipe_bev);

    DEBUG(PIPE_WRITE, "data=%p, len=%d", data, len);

    DEBUG(PIPE_WRITE, "bufferevent_write(write_pipe, %d)", len);
    if (bufferevent_write(write_pipe_bev, data, len))
        die("bufferevent_write(write_pipe)");
}


/* open/close functions */
void read_fifo_open () {
    // open the read fifo
    DEBUG(FIFO_OPEN, "open(\"%s\", O_RDONLY | O_NONBLOCK)", READ_FIFO_PATH);
    read_fifo_fd = open(READ_FIFO_PATH, O_RDONLY | O_NONBLOCK);

    if (read_fifo_fd == -1)
        die("open(read_fifo)");

    if (fcntl(read_fifo_fd, F_SETFD, FD_CLOEXEC) == -1)
        die("fcntl(read_fifo, F_SETFD)");
    
    // wait for the write end to be opened and a message to be sent
    DEBUG(FIFO_OPEN, "event_set(read_fifo, EV_READ, read_fifo_handler)");
    event_set(&read_fifo_ev, read_fifo_fd, EV_READ, read_fifo_handler, NULL);
    DEBUG(FIFO_OPEN, "event_add(read_fifo)");

    if (event_add(&read_fifo_ev, NULL))
        die("event_add(read_fifo_ev)");
}

void read_fifo_close () {
    if (read_fifo_fd) {
        DEBUG(FIFO_CLOSE, "close(read_fifo)");

        if (close(read_fifo_fd))
            die("close(read_fifo)");

        read_fifo_fd = 0;
    }
}

void write_fifo_open () {
    // open the write fifo
    DEBUG(FIFO_OPEN, "open(\"%s\", O_WRONLY | O_NONBLOCK)", WRITE_FIFO_PATH);
    write_fifo_fd = open(WRITE_FIFO_PATH, O_WRONLY | O_NONBLOCK);

    if (write_fifo_fd == -1)
        die("open(write_fifo)");
    
    if (fcntl(write_fifo_fd, F_SETFD, FD_CLOEXEC) == -1)
        die("fcntl(read_fifo, F_SETFD)");
    
    // set up the write bufferevent
    DEBUG(FIFO_OPEN, "bufferevent_new(write_fifo)");
    write_fifo_bev = bufferevent_new(write_fifo_fd, NULL, NULL, write_fifo_error, NULL);

    if (write_fifo_bev == NULL)
        die("bufferevent_new(write_fifo)");
    
    // and we can enable it already
    DEBUG(FIFO_OPEN, "bufferevent_enable(write_fifo, EV_WRITE)");
    if (bufferevent_enable(write_fifo_bev, EV_WRITE))
        die("bufferevent_enable(write_fifo)");
}

void write_fifo_close () {
    if (write_fifo_bev) {
        DEBUG(FIFO_CLOSE, "bufferevent_disable(write_fifo)");
        if (bufferevent_disable(write_fifo_bev, EV_WRITE))
            die("bufferevent_disable(write_fifo)");
        
        DEBUG(FIFO_CLOSE, "bufferevent_free(write_fifo)");
        bufferevent_free(write_fifo_bev);

        write_fifo_bev = NULL;
    }

    if (write_fifo_fd) {
        DEBUG(FIFO_CLOSE, "close(write_fifo");
        if (close(write_fifo_fd))
            die("close(write_fifo)");

        write_fifo_fd = 0;
    }
}

/* set up the SIGCHLD handler to watch over our child process */
void sigchld_handler_init () {
    DEBUG(SIGCHLD_DEBUG, "event_set(sigchld, SIGCHLD, sigchld_handler)");
    event_set(&sigchld_ev, SIGCHLD, EV_SIGNAL|EV_PERSIST, sigchld_handler, NULL);

    DEBUG(SIGCHLD_DEBUG, "event_add(sigchld)");
    event_add(&sigchld_ev, NULL);
}

/* set up the read/write handlers for a child process */
void process_pipes_init (const struct process_info *pinfo) {
    DEBUG(PIPE_OPEN, "stdin=%d, stdout=%d, stderr=%d", pinfo->stdin_fd, pinfo->stdout_fd, pinfo->stderr_fd);
    
    // the read events
    DEBUG(PIPE_OPEN, "event_set(stdout_pipe, EV_READ, read_pipe_handler, CMD_OUT_DATA_STDOUT");
    event_set(&stdout_pipe_ev, pinfo->stdout_fd, EV_READ, read_pipe_handler, &_stdout_data_cmd);

    DEBUG(PIPE_OPEN, "event_set(stderr_pipe, EV_READ, read_pipe_handler, CMD_OUT_DATA_STDERR");
    event_set(&stderr_pipe_ev, pinfo->stderr_fd, EV_READ, read_pipe_handler, &_stderr_data_cmd);

    DEBUG(PIPE_OPEN, "event_add(stdout_pipe)");
    event_add(&stdout_pipe_ev, NULL);

    DEBUG(PIPE_OPEN, "event_add(stderr_pipe)");
    event_add(&stderr_pipe_ev, NULL);
    
    // set up the write bufferevent
    DEBUG(PIPE_OPEN, "bufferevent_new(stdin_pipe)");
    write_pipe_bev = bufferevent_new(pinfo->stdin_fd, NULL, NULL, write_pipe_error, NULL);

    if (write_pipe_bev == NULL)
        die("bufferevent_new(write_pipe)");
    
    // and we can enable it already
    DEBUG(PIPE_OPEN, "bufferevent_enable(stdin_pipe, EV_WRITE)");
    if (bufferevent_enable(write_pipe_bev, EV_WRITE))
        die("bufferevent_enable(write_pipe)");
}

void write_pipe_close () {
    if (write_pipe_bev) {
        int fd = EVENT_FD(&write_pipe_bev->ev_write);

        DEBUG(PIPE_CLOSE, "bufferevent_disable(write_pipe)");
        if (bufferevent_disable(write_pipe_bev, EV_WRITE))
            die("bufferevent_disable(write_pipe)");
        
        DEBUG(PIPE_CLOSE, "bufferevent_free(write_pipe)");
        bufferevent_free(write_pipe_bev);

        write_pipe_bev = NULL;

        DEBUG(PIPE_CLOSE, "close(write_pipe -> %d)", fd);
        if (close(fd))
            die("close(write_pipe)");
    }
}

/* state functions */
void st_hello_enter () {
    // we wait for the manager to take inital contact with us
    _state = STATE_HELLO;
    
    DEBUG(STATE, "enter");

    // open the fifo and wait for the manager to take contact
    read_fifo_open();
}

void st_recover_enter () {
    // we wait for the manager to contact us again.
    _state = STATE_RECOVER;

    DEBUG(STATE, "enter");
    
    // reopen the fifo and wait for the manager to take contact
    read_fifo_open();
}

void st_idle_enter () {
    // we just wait for the manager to do something
    _state = STATE_IDLE;
    
    DEBUG(STATE, "enter");
}

void st_run_enter () {
    // tend to the processs
    _state = STATE_RUN;

    DEBUG(STATE, "enter");
}

/* command functions */

/*
 * we are in hello/reocver state and have just re-opened the read fifo, the write fifo is still closed.
 * the manager sends us a hello message to indicate that is has our write fifo open.
 */
void cmd_hello (msg_t *msg) {
    ERROR_IF(ERROR_CMD_ARGS_SIZE, msg->len != 1);

    unsigned char version = msg->data[0];

    // the manager has sent us the hello message
    DEBUG(CMD_HELLO, "version=0x%02X", version);

    // now we should be able to open the write as well
    write_fifo_open();

    // and send the reply
    DEBUG(CMD_HELLO, "reply with version=0x%02X", PROTOCOL_VERSION);
    protocol_reply(REPLY_HELLO, PROTOCOL_VERSION);

    // now we change state, depending on where we were
    if (_state == STATE_HELLO) {
        // no process running
        st_idle_enter();
    } else if (_state == STATE_RECOVER) {
        // a process was running when the manager disconnected
        st_run_enter();
    } else {
        assert(0);
    }
}

/*
 * we are in the idle state with no process running.
 * start up the process
 */
void cmd_start (msg_t *msg) {
    ERROR_IF(ERROR_CMD_ARGS_SIZE, msg->len > MAX_DATA_LEN - 1);

    char *args[MAX_ARGS];
    
    unsigned char *data = (unsigned char *) msg->data, *data_p = data, arg_count = *data_p++;

    DEBUG(CMD_START, "arg_count=%d", arg_count);

    ERROR_IF(ERROR_CMD_START_ARGS_COUNT, arg_count > MAX_ARGS);
    
    int arg;
    for (arg = 0; arg < arg_count; arg++) {
        unsigned char arg_len = *data_p;
        
        // store a pointer into msg->data into the args array
        args[arg] = data_p + 1;

        // add a null terminator for the preceeding string
        *data_p = '\0';

        data_p += arg_len;
    }

    // null terminator for the final arg string
    data[msg->len] = '\0';

    // and the terminating NULL for args
    args[arg_count] = NULL;
    
    for (arg = 0; arg < arg_count; arg++) {
        DEBUG(CMD_START, " arg %d: %s", arg, args[arg]);
    }
    
    // do the process creation
    const struct process_info *pinfo = process_create(args);

    // send back the reply
    if (!pinfo) {
        protocol_error(ERROR_PROCESS_ALREADY_RUNNING);

    } else if (pinfo->status == PROC_ERR) {
        DEBUG(CMD_START, "    PROC_ERR: %s: %s", pinfo->errmsg, strerror(pinfo->errnum));
        protocol_error(ERROR_CMD_PROCESS_INTERNAL);

    } else {
        DEBUG(CMD_START, "success");

        process_pipes_init(pinfo);
        st_run_enter();

        protocol_reply(REPLY_SUCCESS, 0);
    }
}

/*
 * simply send the given signal to the process
 */
void cmd_kill (msg_t *msg) {
    ERROR_IF(ERROR_CMD_ARGS_SIZE, msg->len != 1);

    unsigned char sig = ((unsigned char *) msg->data)[0];
    
    DEBUG(CMD_KILL, "process_kill(%d)", sig);
    const struct process_info *pinfo = process_kill(sig);

    if (!pinfo) {
        protocol_error(ERROR_PROCESS_NOT_RUNNING);

    } else if (pinfo->status == PROC_ERR) {
        DEBUG(CMD_KILL, "PROC_ERR: %s: %s", pinfo->errmsg, strerror(pinfo->errnum));
        protocol_error(ERROR_CMD_PROCESS_INTERNAL);

    } else {
        DEBUG(CMD_KILL, "success");
        protocol_reply(REPLY_SUCCESS, 0);
    }
}

/*
 * query for process status
 */
void cmd_query_status (msg_t *msg) {
    const struct process_info *pinfo = process_status();

    short code, data;

    _proc_status_to_reply(pinfo, &code, &data);
    
    DEBUG(CMD_STATUS, "process_status is 0x%02X %d", code, data);

    protocol_reply(code, data);
}

/*
 * send data to the process
 */
void cmd_data_stdin (msg_t *msg) {
    DEBUG(CMD_STDIN, "write len=%d", msg->len);
    write_pipe_send(msg->data, msg->len);

    protocol_reply(REPLY_SUCCESS, 0);
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
    process_init();
    event_init();
    sigchld_handler_init();

    // enter init phase
    st_hello_enter();
    
    // run the event dispatcher until completion.
    DEBUG(MAIN, "event_dispatch() ...");
    int err = event_dispatch();

    // inspect the error code... WTF is it?
    DEBUG(MAIN, "event_dispatch -> err=%d", err);
    
    return 0;
}
