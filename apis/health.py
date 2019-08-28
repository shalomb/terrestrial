#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from flask import Blueprint, Flask, json, request, make_response
from flask_restplus import Api, Namespace, Resource, fields

from http import HTTPStatus

import datetime

api = Namespace('', description='Service Availability Namespace')

# api_v1 = Blueprint('api', __name__, url_prefix='/api/v1')
# api.register_blueprint(api_v1)

hc_fields = api.model('HCModel', {
  'http_status': fields.Integer(min=200, max=299, required=False, description='HTTP Status Code to Return')
})

@api.route('/healthz')
@api.doc(
  get={'params': {'http_status': 'HTTP Status Code to return'}}
)
class HealthzWithStatus(Resource):

  @api.doc(
    id='Test Service Health',
    description='''
    Endpoint to test service aliveness.
    ''',
  )
  @api.response(200, 'Success',
    headers={
      'X-HTTPStatus-Code': 'HTTP Status Code requested by downstream (default=200)',
      'X-HTTPStatus-Text': 'HTTP Status Code Text/Reason (RFC 7231)'
    }
  )
  def get(self):
    http_status = 200

    try:
      http_status = int(request.args.get('http_status', 200))
    except Exception:
      pass

    try:
      desc = HTTPStatus(http_status).name
    except Exception as e:
      desc = str(e)

    r = make_response('', http_status)

    r.headers['X-HTTPStatus-Code'] = http_status
    r.headers['X-HTTPStatus-Text'] = desc

    return r

