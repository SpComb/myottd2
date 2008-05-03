#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

#define OTTD_UID 103
#define OTTD_DIR "/ottd"
#define OTTD_PATH "/ottd/openttd"
#define OTTD_NAME "openttd"
#define OTTD_ARGS "-D"

/* perror + exit */
void die (char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

/* exec openttd */
void ottd_exec () {
    if (setuid(OTTD_UID) != 0) die("setuid");
    if (chdir(OTTD_DIR) != 0) die("chdir");

    printf("[ottd]: pid=%d, uid=%d\n", getpid(), getuid());
    printf("[ottd]: redirecting stdin/out\n");

    if (freopen(OTTD_CONSOLE_IN, "r", stdin) == NULL) die("freopen stdin");
    if (freopen(OTTD_CONSOLE_OUT, "w", stdout) == NULL) die("freopen stdout");
    if (freopen(OTTD_CONSOLE_OUT, "w", stderr) == NULL) die("freopen stderr");

    printf("[ottd]: console open\n");

    execl(OTTD_PATH, OTTD_NAME, OTTD_ARGS, NULL);
    
    /* execl can't return a non-error... */
    die("execl");
}

/* stop */
void shutdown (int signal) {
    printf("[init]: shutdown\n");

    kill(-1, SIGTERM);
    kill(-1, SIGKILL);
}

void sig_chld (int signal) {
    printf("[init]: SIGCHLD\n");
}

/* start */
int main () {
    pid_t child, ret;

    if (printf("[init]: pid=%d, uid=%d\n", getpid(), getuid()) < 0) die("printf");
    
    /* signal for stop */
    signal(SIGINT, &shutdown);
    // signal(SIGCHLD, &sig_chld); /* waitpid should take care of this */
    
    /* child process for ottd */
    if ((child = fork()) == -1) die("fork");

    if (child) {
        if (printf("[init]: fork=%d\n", child) < 0) die("printf");
        if (printf("[init]: closing stdin/out/err\n") < 0) die("printf");
        
        fclose(stdin);
        fclose(stdout);
        fclose(stderr);

        /* wait for openttd */
        if ((ret = waitpid(child, NULL, 0)) < 0) die("waitpid");
        
        // XXX: Figure out logging (a logfile?)
        // if (printf("[init]: waitpid=%d\n", ret) < 0) die("printf");

    } else {
        ottd_exec();

        /* this should never return */
    }
    
    return 0;
}

