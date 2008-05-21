/*
 * The code for daemon that handles the subprocess
 */

#include <sys/types.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <assert.h>
#include <stdio.h>

#include "process.h"

// the global process_info struct
static struct process_info _process;

// internal prototypes
void _process_exec (int pipefds[3][2], char *const argv[]);

/* functions */

/*
 * simple initialization of state
 */
void process_init () {
    // clear the _process
    memset(&_process, 0, sizeof(_process));
};

/*
 * fork off a new process and provide some info about it.
 */
const struct process_info *process_create (char *args[MAX_ARGS]) {
    #define RETURN_ERROR(msg) do { _process.errmsg = msg; _process.errnum = errno; _process.status = PROC_ERR; return &_process; } while (0)

    #define PIPE_READ 0
    #define PIPE_WRITE 1

    if (_process.pid) {
        // a process is already running...
        return NULL;
    }
    
    // clear the _process
    process_init();

    // prepare the real arguments
    char *argv[MAX_ARGS];

    argv[0] = EXEC_NAME;

    int i;
    for (i = 0; i < MAX_ARGS; i++)
        if (args[i] == NULL)
            break;
        else
            argv[i + 1] = args[i];
    
    argv[i + 1] = NULL;

    // first, we must create the pipes.
    int pipefds[3][2];

    if (
        (pipe(pipefds[ STDIN_FILENO  ]) == -1) ||
        (pipe(pipefds[ STDOUT_FILENO ]) == -1) ||
        (pipe(pipefds[ STDERR_FILENO ]) == -1)
    ) 
        RETURN_ERROR("pipe");
        
    
    // then, we fork
    _process.pid = fork();

    if (_process.pid == -1)
        RETURN_ERROR("fork");
    
    if (_process.pid == 0) {
        // child. Note that we can't return anymore, or very weird things would start to happen.
        
        _process_exec(pipefds, argv);

        /* this only returns on an error condition */
        // XXX: need to communicate errmsg/errno back somehow
        _process.status = PROC_ERR;

        FILE *emerg_stderr = fdopen(pipefds[ STDERR_FILENO ][ PIPE_WRITE ], "w");
        
        if (emerg_stderr)
            fprintf(emerg_stderr, "[internal] Startup error: %s: %s\n", _process.errmsg, strerror(_process.errnum));

        exit(EXIT_FAILURE);
    } else {
        // parent
        
        // close the child's pipe-fds
        close(pipefds[ STDIN_FILENO  ][ PIPE_READ  ]);
        close(pipefds[ STDOUT_FILENO ][ PIPE_WRITE ]);
        close(pipefds[ STDERR_FILENO ][ PIPE_WRITE ]);
        
        // store stuff into the info struct
        _process.stdin_fd  = pipefds[ STDIN_FILENO  ][ PIPE_WRITE ];
        _process.stdout_fd = pipefds[ STDOUT_FILENO ][ PIPE_READ  ];
        _process.stderr_fd = pipefds[ STDERR_FILENO ][ PIPE_READ  ];
        
        // set proc status
        _process.status = PROC_RUN;
        _process.signal = _process.exit_status = 0;
        _process.errnum = 0; _process.errmsg = NULL;

        return &_process;
    }
}

/*
 * this function is run in the child process after fork()
 */
void _process_exec (int pipefds[3][2], char *const argv[]) {
    #define ERROR_RETURN(msg) do { _process.errmsg = msg; _process.errnum = errno; return; } while (0)

    // close the parent's pipe-fds
    if (
        (close(pipefds[ STDIN_FILENO  ][ PIPE_WRITE ]) == -1 ) ||
        (close(pipefds[ STDOUT_FILENO ][ PIPE_READ  ]) == -1 ) ||
        (close(pipefds[ STDERR_FILENO ][ PIPE_READ  ]) == -1 )
    )
        ERROR_RETURN("close");

    // replace our stdin/out/err
    if (
        (dup2(pipefds[ STDIN_FILENO  ][ PIPE_READ  ], STDIN_FILENO ) == -1) ||
        (dup2(pipefds[ STDOUT_FILENO ][ PIPE_WRITE ], STDOUT_FILENO) == -1) ||
        (dup2(pipefds[ STDERR_FILENO ][ PIPE_WRITE ], STDERR_FILENO) == -1)
    ) 
        ERROR_RETURN("dup2");

    // chdir...
    if (chdir(EXEC_CWD) == -1)
        ERROR_RETURN("chdir");

    // and then we exec, hoping for the best. XXX: how is libevent affected by this?
    if (execv(EXEC_PATH, argv) == -1)
        ERROR_RETURN("execv");
    else {
        /* hallelujah! */
        ((short *) 0xDEADBEEF)[1337] = 42;
    }
}

/*
 * Assuming our child process is still alive, signal them with the given signal
 */
const struct process_info *process_kill (int sig) {
    // *whistle*

    if (_process.status != PROC_RUN) {
        return NULL;
    }
    
    if (kill(_process.pid, sig) == -1) {
        _process.status = PROC_ERR;
        _process.errmsg = "kill";
        _process.errnum = errno;
    }

    return &_process;
}

/*
 * Update the status info of current process
 */
const struct process_info *process_status () {
    if (_process.status != PROC_RUN) {
        // don't waitpid() on a nonexistant process
        return &_process;
    }
    
    int status;
    
    // poll the pid with waitpid
    pid_t ret = waitpid(_process.pid, &status, WNOHANG);
    
    if (ret == -1) {
        // waitpid gave an error
        _process.status = PROC_ERR;
        _process.errmsg = "waitpid";
        _process.errnum = errno;

    } else if (ret == 0) {
        // no processes changed state, so status must be PROC_RUN (and so it should stay)
        assert(_process.status == PROC_RUN);

    } else {
        // process has changed state (exited, killed).
        assert(ret == _process.pid);
        
        // zero out the signal and exit_status for clarity
        _process.signal = _process.exit_status = 0;
        
        // mark the pid invalid as it doesn't exist anymore
        _process.pid = 0;

        if (WIFEXITED(status)) {
            _process.status = PROC_EXIT;
            _process.exit_status = WEXITSTATUS(status);
        } else if (WIFSIGNALED(status)) {
            _process.status = PROC_KILLED;
            _process.signal = WTERMSIG(status);
        } else {
            assert(0);
        }
    }

    return &_process;
}

/*
 * Cleans up the info associated with a dead process, closing file descriptors etc.
 * Status info is retained.
 *
 * Only valid for dead processes, not live, running processes.
 */
void process_cleanup () {
    assert(_process.status != PROC_RUN);
    
    #define CLOSE_FD(fd) do { if (fd) { close(fd); fd = 0; } } while (0)
    
    CLOSE_FD(_process.stdin_fd);
    CLOSE_FD(_process.stdout_fd);
    CLOSE_FD(_process.stderr_fd);
}
