# This package is intended to be used for integration tests - a type of test that couples more tightly into
# environment - has access to database, actually runs web server in backend and so forth.
# Such tests usually have broader coverage (i.e. test more code) and closer to actual use cases, but usually
# harder to write, debug and maintain and take significantly longer time to run.
