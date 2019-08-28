#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os

from utils.logger  import setup_logger
log = setup_logger(__name__)

from flask import \
  current_app, Flask, flash, g, has_request_context, jsonify, make_response, \
  redirect, request, \
  render_template, session, url_for, Blueprint
from flask_restplus import Api, fields, Resource, Namespace

from utils.handlers import setup_request_handlers, setup_exception_handlers

import config as cfg


def create_app():
  app = Flask(__name__, instance_relative_config=True)
  app.config.from_pyfile('defaults.py', silent=True)
  app.name = app.config['TITLE']
  app.url_map.strict_slashes = False

  from apis import api
  api.init_app(app)

  api.title       = app.config['TITLE']
  api.description = app.config['DESCRIPTION']
  api.version     = app.config['VERSION']
  api.doc         = app.config['DOC_PATH']
  api.contact     = app.config['CONTACT']

  setup_request_handlers(app)
  setup_exception_handlers(app, api)

  return app

def main():
  log.info('Initializing app')
  app = create_app()

  if os.environ.get('DEBUG', False):
    app.run(debug=True)
  elif os.environ.get('ENV', '') == 'PROD':
    from waitress import serve
    import logging
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)
    serve(app, listen='0.0.0.0:8080', url_scheme='http')
  else:
    app.run()

if __name__ == '__main__':
  main()

