#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from celery.exceptions import SoftTimeLimitExceeded, Ignore
from celery.task.control import revoke
from flask import Blueprint, Flask, g, jsonify, request, url_for
from flask_restplus import Api, Namespace, Resource, fields
from werkzeug.exceptions import BadRequest

import datetime
import sys
import time
import traceback

from utils.redisdb import RedisDB
from utils.schema_loader import SchemaLoader, cwd, dirname

from .tasks import *

__dir__ = cwd(__file__)

api = Namespace('api/v1', description='LoadBalancer API v1 Namespace')

# api_v1 = Blueprint('api', __name__, url_prefix='/api/v1')
# api.register_blueprint(api_v1)

sl = SchemaLoader(api, dir=__dir__)
lb_resource_model = sl.load_from_file('lb_schema.yaml')

def utcnow():
  return datetime.datetime.utcnow()

class LBController():

  def __init__(self):
    self.db = RedisDB( url=celery.backend.url, db=0 )

  def list_lbs(self):
    return {
      "status": "success",
      "message": "unimplemented"
    }, 200

  def read(self, id):
    if self.db.exists(f'lb/{id}'):
      return self.db.get(f'lb/{id}'), 200
    else:
      return {
        'message': f'LB {id} does not exist or not found'
      }, 404

    try:
      # TODO - If the resource hasn't been created, redirect to the job
      resource = self.db.get(f'lb/{id}')
      return resource, 200
    except KeyError as e:
      pass

  def job_status_repr(self, job):
    return {
      'done':       job.date_done,
      'failed':     job.failed(),
      'id':         job.id,
      'ready':      job.ready(),
      'request_id': self.db.get(f'job/{job.id}/request') if self.db.exists(f'job/{job.id}/request') else None,
      'status':     job.state,
      'successful': job.successful(),
      'url':        url_for('job.status', id=job.id, _external=True),
    }

  def job_revoke(self, id):
    job = celery.AsyncResult(id)

    if job.id:
      last_state = job.state
      revoke(job.id, terminate=True, signal='SIGUSR1')

      for i in range(26):
        time.sleep(1)
        job = celery.AsyncResult(id)
        current_state = job.state

        if current_state != last_state or job.state == 'REVOKED':
          break

      return { 'job_state': self.job_status_repr(job) }, 200
    else:
      return { 'message': f'Job {id} not found' }, 404

  def job_status(self, id):
    job = celery.AsyncResult(id)

    job_state = job.state

    # ACCEPTED is our default state, PENDING implies non-existent task
    if job_state == 'PENDING':
      return { 'message': f'Job {job.id} not found' }, 404

    if job_state == 'REVOKED':
      return { 'job_status': self.job_status_repr(job) }, 200

    job_output = {}
    try:
      if job.ready():
        job_output = job.get(propagate=True)
    except Exception as e:
      exc_type, value, exc_traceback = sys.exc_info()
      job_state = 'Exception'
      job_output = {
        'type': exc_type.__name__,
        'value': str(value),
        'error': str(e),
        'msg': traceback.format_exc().splitlines()[-1]
      }

    job_status = self.job_status_repr(job)
    job_status.update({ 'output': job_output, 'status': job_state })

    if job.successful():
      lb_id = job.id
      resource_location = url_for('lb.resource', id=lb_id, _external=True)
      self.db.set(f'job/{job.id}/result', job_status)
      self.db.set(f'lb/{lb_id}/job/{job.id}', f'job/{job.id}/result')
      # TODO
      # Register resource from task output
      # Define resource schema
      #   - LB configuration
      #   - LB node collection
      #   - LB node details
      self.db.set(f'lb/{lb_id}', {
        'id': lb_id,
        'provider': __name__,
        'url': resource_location,
        'job': job.id,
        'resource': job_status,
      })
      return { 'job_status': job_status }, 303, {
        'Location': resource_location
      }

    return { 'job_status': job_status }, 200

  def job_create(self, payload=None, request_id=None):
    self.db.set(f'request/{request_id}/payload', payload)

    request = {
      'id': request_id,
      'request_time': str(g.request_time),
    }
    self.db.set(f'request/{request_id}', request)

    task = LoadBalancerStack()
    job = task.delay(request_id=request_id)
    self.db.set(f'job/{job.id}/request', request_id)
    r = self.job_status_repr(job)
    r.update({
      'type':   task.__name__,
      'module': sys.modules[__name__].__name__,
      'request_id': request_id,
      'ack_time': str(utcnow()),
    })
    self.db.set(f'request/{request_id}/job', r)

    return { 'job': r }, 202, { 'Location': r['url'] }

ctrl = LBController()

def func(*args, **kwargs):
  print(f'validate func({args}, {kwargs}) ')

@api.route('/lb')
class LBCollection(Resource):

  def validate_payload(self, func):
    try:
      super().validate_payload(func)
    except BadRequest as e:
      msg = e.data if hasattr(e, 'data') else {
              'errors': {
                'InvalidData': 'Empty POST body'
              },
              'message': 'Input payload validation failed'
            }
      api.abort(400, **msg)

  # TODO
  # This requires us to support HTTP authentication
  @api.doc(
    'List load-balancers',
    description='''
    Return a list of the load-balancers created for the current tenant.
    '''
  )
  def get(self):
    return ctrl.list_lbs()

  # TODO
  # Treat the deployment as atomic/transactional - a failure should attempt
  # to clean up all openstack resources if provisioning fails.
  @api.doc(
    id='Create a load-balancer',
    responses={
      202: '[202 Accepted](https://httpstatuses.com/202). Job successfully queued.'
    },
    description='''
    Start a job to deploy a load-balancer using the configuration POSTed.

    Clients should track the status of the job to decide how to continue.

    On job completion with a success status, a 303 (See Other) is returned
    to the location to the created load-balancer resource. Clients should then
    follow to this location to deal with the load-balancer resource.

    On job completion with a failure status, the details of the failure are
    returned for debugging purposes. In this case, no load-balancer resource is
    registered (but openstack resources may continue to exist and no attempt is
    made to clean these up). Clients may POST the request again to attempt to
    re-instantiate the load-balancer (if openstack resources from previous jobs
    exist, they will be reused).
    '''
  )
  @api.expect(lb_resource_model, validate=True)
  # TODO - marshal_with does not work with JSONSchema models
  # @api.marshal_with(lb_resource_model, code=202, envelope='result')
  def post(self):
    return ctrl.job_create(
      payload=api.payload,
      request_id=g.request_id
    )

@api.route('/lb/<string:id>', endpoint='lb.resource')
class LBResource(Resource):

  @api.doc(
    id='Get load-balancer instance',
    responses={200: 'OK'},
    description='''
    TODO: Unimplemented
    Retrieve the configuration pertaining to a load-balancer instance.
    '''
  )
  def get(self, id):
    return { 'message': 'TODO: Functionality unimplemented' }, 405

  @api.doc(
    id='Configure load-balancer instance',
    responses={200: 'OK'},
    description='''
    TODO: Unimplemented
    Update the configuration pertaining to a load-balancer instance.
    '''
  )
  def put(self, id):
    return { 'message': 'TODO: Functionality unimplemented' }, 405

  @api.doc(
    id='Delete load-balancer instance',
    responses={200: 'OK'},
    description='''
    TODO: Unimplemented
    Delete a load-balancer instance and all its nodes.
    '''
  )
  def delete(self, id):
    return { 'message': 'TODO: Functionality unimplemented' }, 405


@api.route('/jobs/<string:id>', endpoint='job.status')
@api.param('id', 'The job identifier (UUID)')
class JobRouter(Resource):

  @api.doc(
    id='Get job status',
    responses={200: 'OK', 303: 'See Other'},
    description='''
    Retrieve the status of a job given its ID.
    If the job is complete and successful, a redirect (303 - See Other) is
    made to the created resource.
    '''
  )
  def get(self, id):
    return ctrl.job_status(id)

  @api.doc(
    id='Cancel job',
    responses={200: 'OK', 404: 'Not Found'},
    description='''
    Revoke and terminate a given job.
    '''
  )
  def delete(self, id):
    return ctrl.job_revoke(id)

