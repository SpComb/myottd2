#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define MAX_ARGS 10
#define TARGET "/home/terom/myottd-dev/mvsrvd/scripts/%s-server.sh"
#define TARGET_SIZE 128

int main (int argc, char **argv) {
    char *env[1] = { NULL };
    char target[TARGET_SIZE];

    if (argc < 3) {
        fprintf(stderr, "%s <action> <srv_name> [<args>...]\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    #define CMD(name) (strcmp(argv[1], name) == 0)

    if (!(
        CMD("create") ||
        CMD("start") ||
        CMD("stop") ||
        CMD("destroy")
    )) {
        fprintf(stderr, "Invalid action '%s'\n", argv[1]);
        exit(EXIT_FAILURE);
    }

    if (strlen(TARGET) + strlen(argv[1]) + 16 > TARGET_SIZE) {
        fprintf(stderr, "Target-overflow\n");
        exit(EXIT_FAILURE);
    }
        
    snprintf(target, TARGET_SIZE, TARGET, argv[1]);

    argv[1] = target;

    if ((setuid(0)) == -1) {
        perror("setuid");
        exit(EXIT_FAILURE);
    };

    execve(target, argv + 1, env);
    
    perror("execve");
    return EXIT_FAILURE;
}
