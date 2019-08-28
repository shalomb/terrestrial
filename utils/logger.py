#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import logging
import logging.handlers
import sys
import syslog

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def setup_logger(name=None, logger=None, level=logging.INFO):
  name = name or __name__
  logger = logger or logging.getLogger(name)
  logger.setLevel(level)
  # TODO
  # Consider using a different output device for container deployments
  # e.g. /dev/stdout if at all it is accessible
  handler = logging.handlers.SysLogHandler(
              address  = '/dev/log',
              facility = syslog.LOG_LOCAL0
            )
  formatter = logging.Formatter(f'{name}[%(process)d] %(levelname)s %(name)s %(module)s.%(funcName)s:  %(message)s')
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  return logger

