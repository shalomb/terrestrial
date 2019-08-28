#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
from shutil import copytree, ignore_patterns, rmtree
import tempfile
import subprocess

class IsolatedWorkspace():
  '''
  Setup a temporary workspace context with the following set.
    - clone of repo
    - current working directory
    - process environment variables
  '''

  def __init__(self, parent, cwd=None, env={}):
    self.parent = parent
    self.oldpwd = os.getcwd()
    self.oldenv = os.environ.copy()
    self.cwd = cwd
    self.env = env
    self.instance = None

  def __enter__(self):
    self.instance = self.cwd or tempfile.TemporaryDirectory().name
    copytree(
      self.parent,
      self.instance,
      # Ignore tempfiles, ssh sockets, etc
      ignore=ignore_patterns('*.pyc', 'tmp*', '.ssh*')
    )
    if self.env:
      os.environ.update( self.env )
    os.chdir(self.instance)
    return os.getcwd()

  def __exit__(self, exc, value, traceback):
    os.environ.clear()
    os.environ.update(self.oldenv)
    os.chdir(self.oldpwd)
    print(f'Keeping {self.instance}')
    # rmtree(self.instance)
    return False if exc else True

