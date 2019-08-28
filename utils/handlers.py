#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from flask import g, has_request_context, request
from flask_apiexceptions import (
  JSONExceptionHandler, ApiException, ApiError, api_exception_handler
)

import datetime

def utcnow():
  return datetime.datetime.utcnow()

# TODO Extend error handling to return more semantic information besides
# the regular 500
# http://pycoder.net/bospy/presentation.html#bonus-material
def setup_exception_handlers(app, api):

  @api.errorhandler(Exception)
  def exception_handler(error):
    # print(' EXCEPTION::{}'.format(repr(error)))
    return {}, error.code

  ext = JSONExceptionHandler(app)
  ext.register(code_or_exception=ApiException, handler=api_exception_handler)

def setup_request_handlers(app):

  @app.before_request
  def request_before_handler(*args, **kwargs):

    if has_request_context():
      request_time = request.headers.get('X-Request-Time', utcnow())
      request_id   = request.headers.get(
        'X-Request-Id',
        '{}{}'.format(
          utcnow().strftime('%Y%m%d%H%M%S%f')[0:17],
          str(id(request.headers))[6:]
        )
      )
      g.request_id   = request_id
      g.request_time = request_time
    else:
      raise Exception('Operating outside of a request_context')

  @app.after_request
  def request_after_handler(response, *args, **kwargs):
    if response.headers:
      response.headers['Server'] = app.name
      response.headers['X-Request-Id'] = g.request_id
      response.headers['X-Request-Time'] = g.request_time
      response.headers['X-Request-Duration'] = utcnow() - g.request_time
    return response

