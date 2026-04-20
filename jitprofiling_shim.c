#ifdef __cplusplus
extern "C" {
#endif

static int next_method_id = 1;

int iJIT_NotifyEvent(int event_type, void *event_data) {
    (void)event_type;
    (void)event_data;
    return 0;
}

int iJIT_IsProfilingActive(void) {
    return 0;
}

int iJIT_GetNewMethodID(void) {
    return next_method_id++;
}

#ifdef __cplusplus
}
#endif
