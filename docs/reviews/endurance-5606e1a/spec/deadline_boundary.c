/* Independent deadline edge case. Actual E1 core; simulated time/peripherals. */
#define main archived_model_main
#include "test_core.c"
#undef main

static int jumped;
static uint64_t jump_after_minimum(void *p) {
    struct fake *f = p;
    if (!jumped && f->session->groups >= SHORT_MIN_GROUPS && !f->session->stop_sent) {
        jumped = 1;
        f->time = f->session->start_us + SHORT_RUN_US + TIMEOUT_US + 100;
    }
    return time_us(p);
}

int main(void) {
    struct fake f = {0};
    struct session s;
    session_init(&s);
    f.session = &s;
    struct io io = {&f, jump_after_minimum, source, sr, length, run, arm, prepare, acquire};
    struct segment_config config = {SHORT_RUN_US, SHORT_MIN_GROUPS};
    enum failure result = session_run_config(&s, &io, &config);
    printf("case=resume_after_total_deadline result=%s jumped=%d elapsed_us=%u deadline_us=%u groups=%u packets=%u stop_sent=%d\n",
        failure_name(result), jumped, (unsigned)(s.stop_us - s.start_us),
        SHORT_RUN_US + TIMEOUT_US, s.groups, s.packets, s.stop_sent);
    /* A successful exit means the observed counterexample reproduced, not that
       the deadline implementation passed the intended negative case. */
    return !(jumped && result == OK && s.stop_us - s.start_us > SHORT_RUN_US + TIMEOUT_US);
}
