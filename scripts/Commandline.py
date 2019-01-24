# -*- coding: utf-8 -*-

"""
Functions involving sending commands to the commandline.
"""
import logging
import os
import subprocess as sp

class Commandline:
    """
    This class wraps calls to the command line in a simple interface.
    """

    def __init__(self, name=None, logr_cur=None):
        """
        Initializer that allows one to set the logger.

        * logr_cur : Logger
                     Optional parameter for logging.
                     If supplied this logger will be used,
                     otherwise the root logger will be used.
        """

        self.logr_cur = logr_cur if logr_cur else logging.getLogger(name)


    # Tested
    def func_CMD(self,
                 command,
                 use_bash=False,
                 test=False,
                 stdout=False):
        """
  	    Runs the given command.
        * command : Command to run on the commandline
                      : String
        * use_bash : Boolean
                     : If true, sends the command through using
                       BASH not SH (Bourne) or default shell (windows)
                     : Although the False is _I believe_ is not specific
                       to an OS, True is.
	    * test : Boolean
	               If true, the commands will not run but will be logged.
        * stdout : Boolean
                   : If true, stdout will be given instead of True.
                     On a fail False (boolean) will still be given.
	    * Return : Boolean
	               True indicates success
	      """

        return_code = None

        # Update command for bash shell
        if use_bash:
            command = "".join([os.sep, "bin", os.sep,
                                   "bash -c \'", command, "\'"])

        # Do not do anything when testing
        if test:
            return True

        try:
            # Perform command and wait for completion
            if stdout:
                subp_cur = sp.Popen(command,
                                    shell=True,
                                    cwd=os.getcwd(),
                                    stdout=sp.PIPE)
            else:
                subp_cur = sp.Popen(command, shell=True, cwd=os.getcwd())
            pid = str(subp_cur.pid)

            out, err = subp_cur.communicate()
            return_code = subp_cur.returncode

            # 0 indicates success
            # On Stdout == true return a true string (stdout or 1 blank space)
            if return_code == 0:
                if stdout:
                    return out
                return True
            else:
                self.logr_cur.error("".join([self.__class__.__name__,
                                             "::Error::Received return code = ",
                                             str(return_code)]))
                self.logr_cur.error("".join([self.__class__.__name__,
                                             "::Error::Command = ",
                                             command]))
                self.logr_cur.error("".join([self.__class__.__name__,
                                             "::Error::Error out= ",
                                             str(out)]))
                self.logr_cur.error("".join([self.__class__.__name__,
                                             "::Error::Error= ",
                                             str(err)]))
                return False

        # Inform on errors:w
        except(OSError, TypeError) as e:
            self.logr_cur.error("".join([self.__class__.__name__,
                                         "::Error::Fatal error."]))
            self.logr_cur.error("".join([self.__class__.__name__,
                                         "::Error::Command = ", command]))
            self.logr_cur.error("".join([self.__class__.__name__,
                                         "::Error:: Error = ", str(e)]))
            return False
        return False