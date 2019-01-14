# Non functional requirements

## Run environment

Applications must support execution in Debian (version >= 8) and Debian derived systems (Ubuntu >= 16.04). 

## Python version

Components should be developed in Python >= 2.7 unless underlying infrastructure requires otherwise. 

## Logging

Application must take advantage of existing syslog interface.

## Daemonization

Daemon type of applications must support systemd startup environment and provide necessary means to control them 
in such environment (startup/shutdown scripts etc).
