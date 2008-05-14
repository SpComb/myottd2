#define EXEC_CWD "test/"
#define EXEC_PATH "./test"
#define EXEC_NAME "test"

// maximum number of arguments accepted, including the terminating NULL, but NOT argv[0], i.e. the executable name
#define MAX_ARGS 254

#define PROC_ERR -1
#define PROC_IDLE 0
#define PROC_RUN 1
#define PROC_EXIT 2
#define PROC_KILLED 3


struct process_info {
    pid_t pid;

    int stdin_fd;
    int stdout_fd;
    int stderr_fd;

    /* status info. Duplicates much of waitpid(), but who gives */

    // one of PROC_{ERR,IDLE,RUN,EXIT,SIGNAL}
    int status;
    
    // PROC_EXIT -> a short (one word) description of what failed + value of errno
    int errnum;
    char *errmsg;

    // PROC_EXIT -> process' exit status
    int exit_status;

    // PROC_KILLED -> process' signal fatality
    int signal;
};


void process_init ();
const struct process_info *process_create (char *args[MAX_ARGS]);
const struct process_info *process_kill (int sig);
const struct process_info *process_status ();
void process_cleanup ();

