# An interceptor is a callable that is called at the end of the "init" command.
#
# Interceptors are passed the initialized WorkDB, and they are able to do
# things like mark certain mutations as skipped (i.e. so that they are never
# performed).
