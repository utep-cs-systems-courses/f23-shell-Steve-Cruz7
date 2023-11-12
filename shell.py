#! /usr/bin/env python3

import os, sys, re

pid = os.getpid()
waitForPid = 0
childMap = {}

#Going to use 0 for input and 1 for output

while(True):
    #Implementing waiting for child process
    while(waitForPid):
        waitResult = os.waitid(waitForPid, 0)                        #Ask if a loop is necessary since waitid suspends this process anyways
        if waitResult:
            zPid, zStatus = waitResult.si_pid, waitResult.si_status
            if zPid == waitrForPid:
                waitForPid = None
                del childMap[waitForPid]
                os.write(1, "WaitForPid process complete".encode())
    while childMap.keys():
        waitResult = os.waitid(os.P_ALL, 0, os.WNOHANG | os.WEXITED)
        if waitResult:
            zPid, zStatus = waitResult.si_pid, waitResult.si_status
            del childMap[zPid]
            os.write(1, "Background zombie reaped".encode())
        
        
    os.write(1, "$ ".encode())
    userInput =  os.read(0, 100)               #Take user input. We are going to parse this
    if len(userInput) == 0:
        exit()
    else:
        argv = userInput.decode().replace('\n', '')   #Getting ride of the \n at the end of line

        argv = re.split(" ", argv)         #creating my list of arguments
        for i in range(len(argv)):
            if argv[i] == "exit":
                os.write(1, "Exiting...\n".encode())
                exit()
            elif argv[i] == "cd":                                   
                if len(argv) > i+1:                                               
                     os.chdir(argv[i+1])                                           
                     i = i + 1
            elif argv[i] == "ls":
                os.write(1, "This should print the contents of the current directory".encode())
            elif argv[i] == "cat":
                if len(argv) > i+1:
                    os.write("This should print the contents of whatever file is put".encode())
            else:
                #Going to attempt to execute a file
                fk = os.fork()
                #if child, execute; else,  map child's PID to command string to remember where it was made
                if fk <  0:
                    os.write(2, ("Fork attempt failed, returning %d" % fk).encode())
                elif fk == 0:
                    program = args[i]
                    arguments = args[i+1:]
                    try:
                        os.execve(program, arguments, os.environ)
                    except FileNotFoundError:
                        os.write(2, ("Child failed to exec %s" % program).encode())
                        sys.exit(1)
                else:
                    childMap[fk] = args[i]         #Adding child's pid to map which command it originated from 
                    if(args[i][-1] != "&"):
                        waitForPid = fk
                    else:
                        waitForPid = None
