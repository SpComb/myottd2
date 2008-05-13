/*
 * The code for daemon that handles the subprocess
 */


#define EXEC_CWD "test/"
#define EXEC_PATH "./test"
#define EXEC_NAME "test"

// maximum number of arguments accepted, including the terminating NULL, but NOT argv[0], i.e. the executable name
#define ARGS_MAX 254


struct process_info {
    // -1 on error
    pid_t pid;

    int stdin_fd;
    int stdout_fd;
    int stderr_fd;
    
    // a short (one word) description of what failed, assuming pid = -1
    char *errmsg;

    // the process's arguments (including argv[0], so this is MAX_ARGS + 1 long]
    char *argv[MAX_ARGS + 1];
};

static process_info _process = { 0, 0, 0, 0, NULL };

#define PIPE_READ 0
#define PIPE_WRITE 1

#define RETURN_ERROR(msg) do { _process.errmsg = msg; return &_process; } while (0)

/*
 * fork off a new process and provide some info about it.
 */
const struct process_info *process_create (const char *args[MAX_ARGS]) {
    if (_process.pid) {
        // a process is already running...
        static struct process_info duplicate;

        duplicate.pid = -1;
        duplicate.errmsg = "already running";

        return &duplicate;
    }

    // prepare the real arguments
    _process.argv[0] = EXEC_NAME;

    int i;
    for (i = 0; i < MAX_ARGS; i++)
        if (args[i] == NULL)
            break;
        else
            _process.argv[i + 1] = args[i];
    
    _process.argv[i + 1] = NULL;

    // first, we must create the pipes.
    int pipefds[3][2];

    if (
        (pipe(pipefds[ STDIN_FILENO  ]) == -1) ||
        (pipe(pipefds[ STDOUT_FILENO ]) == -1) ||
        (pipe(pipefds[ STDERR_FILENO ]) == -1)
    ) else
        RETURN_ERROR("pipe");
        
    
    // then, we fork
    _process.pid = fork();

    if (_process.pid == -1)
        RETURN_ERROR("fork");
    
    if (pid == 0) {
        // child. Note that we can't return anymore, or very weird things would start to happen.
        
        _process_exec(pipefds);

        /* this only returns on an error condition */
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

        return 
    }
}

void _process_exec (int pipefds[3][2]) {
    // close the parent's pipe-fds
    if (
        (close(pipefds[ STDIN_FILENO  ][ PIPE_WRITE ]) == -1 ) ||
        (close(pipefds[ STDOUT_FILENO ][ PIPE_READ  ]) == -1 ) ||
        (close(pipefds[ STDERR_FILENO ][ PIPE_READ  ]) == -1 )
    ) {
        perror("[myottd] close");
        exit(EXIT_FAILURE);
    }

    // replace our stdin/out/err
    if (
        (dup2(pipefds[ STDIN_FILENO  ][ PIPE_READ  ], STDIN_FILENO ) == -1) ||
        (dup2(pipefds[ STDOUT_FILENO ][ PIPE_WRITE ], STDOUT_FILENO) == -1) ||
        (dup2(pipefds[ STDERR_FILENO ][ PIPE_WRITE ], STDERR_FILENO) == -1)
    ) {
        perror("[myottd] dup2");
        exit(EXIT_FAILURE);
    }

    // chdir...
    if (chdir(EXEC_CWD) == -1) {
        perror("[myottd] chdir");
        exit(EXIT_FAILURE);
    }

    // and then we exec, hoping for the best. XXX: how is libevent affected by this?
    if (execv(EXEC_PATH, _process.argv) == -1) {
        perror("[myottd] execv");
        exit(EXIT_FAILURE);
    } else {
        /* hallelujah! */
        ((short *) 0xDEADBEEF)[1337] = 42;
    }
}

int process_kill () {
    
}

