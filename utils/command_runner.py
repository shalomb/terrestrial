#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from datetime import datetime
from os import environ
import subprocess
import tempfile
import logging

def run( cmd=[],
          stdin=subprocess.PIPE,
          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
          timeout=7200, encoding='UTF-8',
          universal_newlines=True, shell=False,
          env={}, cwd=tempfile.TemporaryDirectory().name,
          logger=logging.getLogger(__name__),
          **kwargs
  ):

  # Ensure env vars set in env take precedence over those set in os.environ
  env = { **environ.copy(),
          **{ k: env.get(k, environ.get(k, '')) for k in
                [ 'HOME', 'HOSTNAME', 'PATH', 'PWD', 'TMP' ]
            },
          **env
  }
  kwargs.update({ 'env': env })

  proc = subprocess.Popen(
    cmd,
    stdout   = subprocess.PIPE,
    stderr   = subprocess.PIPE,
    cwd      = cwd,
    encoding = encoding,
    shell    = shell,
    universal_newlines = universal_newlines,
    **kwargs
  )
  # close_fds = True
  # preexec_fn

  start_time = datetime.utcnow()
  try:
    stdout, stderr = proc.communicate(timeout=timeout)
    rc = proc.returncode
    stdout = stdout.split('\n')
    stderr = stderr.split('\n')
  except Exception as e:
    msg = f'ERROR: Exception raised running "{cmd}": {str(e)}'
    logger.error(msd)
    raise Exception(msg) from e
  end_time = datetime.utcnow()

  return {
    'cmd': str(cmd),
    'cwd': cwd,
    'duration': str(end_time - start_time),
    'end': str(end_time),
    'env': env,
    'exit_status': rc,
    'rc': rc,
    'start':  str(start_time),
    'stderr': stderr,
    'stdout': stdout,
  }


