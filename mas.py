#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  This software, having been partly or wholly developed and/or
  sponsored by KoreLogic, Inc., is hereby released under the terms
  and conditions set forth in the project's "README.LICENSE" file.
  For a list of all contributors and sponsors, please refer to the
  project's "README.CREDITS" file.
"""

__doc__ = """
MASTIFF - MAlicious Static Inspection File Framework

This program implements the code necessary to statically analyze files within
a plugin-based framework.

"""

__version__ = "$Id$"

import sys
import logging
import os
import os.path
#import signal

if sys.version_info < (2, 6, 6):
    sys.stderr.write("Mastiff requires python version 2.6.6")
    sys.exit(1)

from optparse import OptionParser, OptionGroup
import mastiff.core as Mastiff
from mastiff import get_release_string
import mastiff.queue as queue

def add_to_queue(job_queue, fname):
    """ Add file and/or directory to job queue. """
    
    log = logging.getLogger('Mastiff.queue')
    # check to see if we are dealing with a directory or a file and handle correctly
    if os.path.isdir(fname) is True:
        # This is a directory - walk it and add all its files
        log.info('Adding directory %s to queue.' % fname)
        for root, _, files in os.walk(fname):
            for new_file in [ os.path.abspath(root + os.sep + f) for f in files]:
                log.debug('Adding %s to job queue.' % new_file )
                job_queue.append(new_file)
    elif os.path.isfile(fname) is True:
        # dealing with a file - just add it to the queue
        log.debug('Adding file %s to job queue.' % fname)
        job_queue.append(fname)
    else:
        log.error('Submission is neither file or directory. Exiting.')
        sys.exit(1)
        
def analyze_file(fname, opts, loglevel):
    """ Analyze a file with MASTIFF. """
    
    log = logging.getLogger('Mastiff.analyze')
    log.info("Starting analysis on %s", fname)
        
    my_analysis = Mastiff.Mastiff(opts.config_file, loglevel=loglevel, override=opts.override)
    if opts.ftype is not None:
        log.info('Forcing file type to include "%s"', opts.ftype)
        my_analysis.set_filetype(fname=fname, ftype=opts.ftype)
    
    my_analysis.analyze(fname,  opts.plugin_name)
    
def main():
    """Parse options and analyze file."""

    usage = "usage: %prog [options] FILE|DIRECTORY"
    parser = OptionParser(
                     add_help_option = False,
                     version = "%prog " + get_release_string(),
                     usage = usage)
    parser.remove_option("--version")
    
    parser.add_option(
                     "--conf",
                     "-c",
                      action = "store",
                      default = "./mastiff.conf",
                      dest = "config_file",
                      help = "Use an alternate config file. The default is './mastiff.conf'.",
                      type = "string")
    parser.add_option(
                      "--help",
                      "-h",
                      action = "help",
                      help = "Show the help message and exit.")
    parser.add_option(
                      "--list",
                      "-l",
                      action = "store",
                      dest = "list_plugins",
                      help = "List all available plug-ins of the specified type and exit. Type must be one of 'analysis', 'cat', or 'output'.",
                      metavar = "PLUGIN_TYPE")
    parser.add_option(
                      "--option",
                      "-o",
                      action="append",
                      default = None,
                      dest = "override",
                      help = "Override a config file option. Configuration options should be specified as 'Section.Key=Value' and should be quoted if any whitespace is present. Multiple overrides can be specified by using multiple '-o' options.")
    parser.add_option(
                      "--plugin",
                      "-p",
                      action = "store",
                      default = None,
                      dest = "plugin_name",
                      help = "Only run the specified analysis plug-in. Name must be quoted if it contains whitespace.")
    parser.add_option(
                      "--quiet",
                      "-q",
                      action = "store_true",
                      default = False,
                      dest = "quiet",
                      help = "Only log errors.")
    parser.add_option(
                      "--type",
                      "-t",
                      action = "store",
                      default = None,
                      dest = "ftype",
                      help = "Force file to be analyzed with plug-ins from the specified category (e.g., EXE, PDF, etc.). Run with '-l cat' to list all available category plug-ins.",
                      type = "string")
    parser.add_option(
                      "--verbose",
                      "-V",
                      action = "store_true",
                      dest = "verbose",
                      default = False,
                      help = "Print verbose logs.")
    parser.add_option(
                      "--version",
                      "-v",
                      action = "version",
                      help = "Show program's version number and exit.")
    
    queue_group = OptionGroup(parser, "Queue Options")
    queue_group.add_option(
                      "--append-queue",
                      "",
                      action = "store_true",
                      dest = "append_queue",
                      default = False,
                      help = "Append file or directory to job queue and exit.")
    queue_group.add_option(
                      "--clear-queue",
                      "",
                      action = "store_true",
                      dest = "clear_queue",
                      default = False,
                      help = "Clear job queue and exit.")
    queue_group.add_option(
                      "--ignore-queue",
                      "",
                      action = "store_true",
                      dest = "ignore_queue",
                      default = False,
                      help = "Ignore the job queue and just process file.")   
    queue_group.add_option(
                      "--list-queue",
                      "",
                      action = "store_true",
                      dest = "list_queue",
                      default = False,
                      help = "List the contents of the job queue and exit.")
    queue_group.add_option(
                      "--resume-queue",
                      action = "store_true",
                      default = False,
                      dest = "resume_queue",
                      help = "Continue processing the queue.")
    parser.add_option_group(queue_group)

    (opts, args) = parser.parse_args()

    if (args is None or len(args) < 1) and opts.list_plugins is None \
    and opts.clear_queue is False and opts.resume_queue is False \
    and opts.list_queue is False:
        parser.print_help()
        sys.exit(1)

    if opts.verbose == True:
        loglevel = logging.DEBUG
    elif opts.quiet == True:
        loglevel = logging.ERROR
    else:
        loglevel = logging.INFO
        
    format_ = '[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s'        
    logging.basicConfig(format=format_)
    log = logging.getLogger("Mastiff")
    log.setLevel(loglevel)

    # check to see if we are running as root
    if os.geteuid() == 0:
        log.warning('You are running MASTIFF as ROOT! This may be DANGEROUS!')

    if opts.list_plugins is not None:
        plugs = Mastiff.Mastiff(opts.config_file)
        plugs.list_plugins(opts.list_plugins)
        sys.exit(0)

    # set up job queue
    job_queue = queue.MastiffQueue(opts.config_file)
    
    # process job queue specific options
    if opts.clear_queue is True:
        log.info('Clearing job queue and exiting.')
        job_queue.clear_queue()
        sys.exit(0)
    elif opts.list_queue is True:
        if len(job_queue) == 0:
            log.info("MASTIFF job queue is empty.")
        else:
            log.info("MASTIFF job queue has %d entries." % len(job_queue))
            print "\nFile Name\n---------\n%s" % (job_queue)            
        sys.exit(0)
        
    if len(args) > 0:
        fname = args[0]
    else:
        fname = None
        
    if opts.ignore_queue is True:        
        log.info('Ignoring job queue.')
        analyze_file(fname,  opts,  loglevel)
        sys.exit(0)

    # add file or directory to queue
    if fname is not None:
        add_to_queue(job_queue, fname)
        if opts.append_queue is True:
            sys.exit(0)    

    # Start analysis on the files in the queue until it is empty
    while len(job_queue) > 0:
        fname = job_queue.popleft()
        analyze_file(fname, opts, loglevel)        
        log.info('There are %d jobs in the queue.' % len(job_queue))

if __name__ == '__main__':

    main()

