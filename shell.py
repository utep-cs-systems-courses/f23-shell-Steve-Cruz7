#! /usr/bin/env python3

import os, sys, re

pid = os.getpid()
waitForPid = 0
childMap = {}

#Going to use 0 for input and 1 for output

while(True):
    while childMap.keys():
        if(waitForPid != None):
            waitResult = os.waitid(os.P_ALL, waitForPid, os.WEXITED)        #Waiting on child process to complete before proceeding
            zPid, zStatus = waitResult.si_pid, waitResult.si_status
            del childMap[waitForPid]
            waitForPid = None
            os.write(1, "Non-background zombie reaped\n".encode())
        else:
            waitResult = os.waitid(os.P_ALL, 0, os.WNOHANG | os.WEXITED)   #If background process, not hanging
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
                    program = argv[i]
                    arguments = argv[i+1:]
                    try:
                        os.execve(program, arguments, os.environ)
                    except FileNotFoundError:
                        os.write(2, ("Child failed to exec %s" % program).encode())
                        sys.exit(1)
                else:
                    childMap[fk] = argv[i]         #Adding child's pid to map which command it originated from 
                    if(argv[i][-1] != "&"):
                        waitForPid = fk
                    else:
                        waitForPid = None
