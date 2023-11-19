#! /usr/bin/env python3

import os, sys, re

pid = os.getpid()
waitForPid = 0
childMap = {}

#Going to use 0 for input and 1 for output

while(True):
    print("My pid: " + str(os.getpid()) + ", Parent pid: " + str(pid))
    if (pid != os.getpid()):     #protects against naughty children
        sys.exit(1)
    while childMap.keys():
        if(waitForPid != None):
            waitResult = os.waitid(os.P_ALL, waitForPid, os.WEXITED)        #Waiting on child process to complete before proceeding
            zPid, zStatus = waitResult.si_pid, waitResult.si_status
            del childMap[waitForPid]
            waitForPid = None
            #os.write(1, "Non-background zombie reaped\n".encode())
        elif(waitResult := os.waitid(os.P_ALL, 0, os.WNOHANG | os.WEXITED)):      #If background process, not hanging
            zPid, zStatus = waitResult.si_pid, waitResult.si_status
            del childMap[zPid]
            #os.write(1, "Background zombie reaped\n".encode())
        
        
    os.write(1, "$ ".encode())
    userInput =  os.read(0, 100)               #Take user input. We are going to parse this
    if len(userInput) == 0:
        exit()
    else:
        arguments = userInput.decode().replace('\n', '')   #Getting ride of the \n at the end of line

        arguments = re.split(" \| ", arguments)
        #creating my list of arguments split on pipes
        for j in range(len(arguments)):
            if(os.getpid() != pid):
                print("Child process: " + str(os.getpid()) + " exiting")
                sys.exit(1)
            if(len(arguments) > 1):
                pr,pw = os.pipe()
                for f in (pr, pw):
                    os.set_inheritable(f, True)
                    #Now that we've made the pipe, time to send off children to do dirty work
                wc = os.fork()
                if wc < 0:
                    print("Failed to fork")
                    sys.exit(1)
                elif wc == 0:
                    os.close(1)
                    os.dup(pw)
                    for fd in (pr, pw):
                        os.close(fd)
                else:
                    j = j + 1
                    rc = os.fork()
                    if rc < 0:
                        print("Failed to fork")
                        sys.exit(1)
                    elif rc == 0:
                        os.close(0)
                        os.dup(pr)
                        for fd in (pw, pr):
                            os.close(fd)
                    else:
                        for fd in (pw, pr):
                            os.close(fd)
                        os.wait()
                            
#Everything past this point has been tested and works
            #print(j)
            args = re.split(" > ", arguments[j])             
            output = None
            if(len(args) > 1):
                output = args.pop(1)         #For now, going to assume only 1 redirect in args
                
            section = re.split(" ", args[0])
            for i in range(len(section)):
                if section[i] == "exit":
                    os.write(1, "Exiting...\n".encode())
                    exit()
                elif section[i] == "cd":                                   
                    if len(section) > i+1:                                               
                        os.chdir(args[i+1])                                           
                        i = i + 1
                elif section[i] == "ls":
                    os.write(1, "This should print the contents of the current directory".encode())
                elif section[i] == "cat":
                    if len(section) > i+1:
                        os.write("This should print the contents of whatever file is put".encode())
                else:
                    #Going to attempt to execute a file
                    fk = os.fork()
                    #if child, execute; else, Im a parent and will  map child's PID to command string to remember where it was made
                    if fk <  0:
                        os.write(2, ("Fork attempt failed, returning %d" % fk).encode())
                        
                    elif fk == 0:
                        if(output != None):  #this means that there is at least 1 > and we need to redirect
                            os.close(1)
                            os.open(output, os.O_CREAT | os.O_WRONLY)               
                            os.set_inheritable(1, True)

                            #the input run.py c 3 > foo.txt would be split into [run.py c 3, foo.txt] and then the first item would be
                            #split into [run.py, c, 3] so we have the program and the rest of the list being its arguments. before splitting that
                            #I make sure to open args[i+1] which in this case is foo.txt before blowing everything away with execve
                            program = section[i]
                            arguments = section[i:]
                            try:
                                os.execve(program, arguments, os.environ)
                            except FileNotFoundError:
                                pass
                            
                        else:
                            program = section[i]
                            arguments = section[i:]
                            try:
                                os.execve(program, arguments, os.environ)
                            except FileNotFoundError:
                                pass
                    else:
                        childMap[fk] = section[i]         #Adding child's pid to map which command it originated from 
                        if(section[i][-1] != "&"):
                            waitForPid = fk
                        else:
                            waitForPid = None
            
