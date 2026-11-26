"""Shared native runtime source for strict, line-oriented numeric input."""
INPUT_RUNTIME = r'''
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>
#include <string.h>
static int bh_input_line(char *s, size_t n) {
    if (!fgets(s, (int)n, stdin)) return 0;
    if (!strchr(s, '\n') && !feof(stdin)) return 0;
    return 1;
}
static int bh_decimal(const char *p, int floating) {
    int digits = 0;
    while (isspace((unsigned char)*p)) ++p;
    if (*p == '+' || *p == '-') ++p;
    while (*p >= '0' && *p <= '9') { ++digits; ++p; }
    if (floating && *p == '.') { ++p; while (*p >= '0' && *p <= '9') { ++digits; ++p; } }
    if (!digits) return 0;
    if (floating && (*p == 'e' || *p == 'E')) {
        int exp_digits = 0; ++p; if (*p == '+' || *p == '-') ++p;
        while (*p >= '0' && *p <= '9') { ++exp_digits; ++p; }
        if (!exp_digits) return 0;
    }
    while (isspace((unsigned char)*p)) ++p;
    return *p == '\0';
}
int bh_read_int(long *value) {
    char line[4096]; char *end;
    if (!bh_input_line(line, sizeof line) || !bh_decimal(line, 0)) return 0;
    errno = 0; *value = strtol(line, &end, 10); return errno != ERANGE;
}
int bh_read_float(double *value) {
    char line[4096]; char *end;
    if (!bh_input_line(line, sizeof line) || !bh_decimal(line, 1)) return 0;
    errno = 0; *value = strtod(line, &end); return errno != ERANGE;
}
'''
