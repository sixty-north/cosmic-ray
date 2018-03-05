from enum import IntEnum


class ExitCode(IntEnum):
    """Exit status codes.

    These mimic those on many unixes (and provided by `os`) but makes them
    available on all platforms.
    """
    # successful termination
    OK = 0

    # command line usage error
    Usage = 64

    # data format error
    DataErr = 65

    # cannot open input
    NoInput = 66

    # addressee unknown
    NoUser = 67

    # host name unknown
    NoHost = 68

    # service unavailable
    Unavailable = 69

    # internal software error
    Software = 70

    # system error (e.g., can't fork)
    OSErr = 71

    # critical OS file missing
    OSFile = 72

    # can't create (user) output file
    CantCreate = 73

    # input/output error
    IOErr = 74

    # temp failure; user is invited to retry
    TempFail = 75

    # remote error in protocol
    Protocol = 76

    # permission denied
    NoPerm = 77

    # configuration error
    Config = 78
