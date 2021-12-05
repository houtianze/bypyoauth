# The server (OAuth) side of bypy.py, the Baidu Personal Cloud Storage python client

import os
import sys
import time
import logging
# import traceback
IsPy2 = sys.version_info[0] == 2
if IsPy2:
	import urllib as ulp
	import urllib2 as ulr
	ule = ulr
else:
	import urllib.parse as ulp
	import urllib.request as ulr
	import urllib.error as ule

from bottle import default_app, route, request, response, run

# constants
ApiKey = os.environ['BAIDU_API_KEY']
SecretKey = os.environ['BAIDU_API_SECRET']
BaiduOpenApiHost = "openapi.baidu.com"
BaiduOAuthPath = "/oauth/2.0/token"
BaiduOAuthUrl = "https://" + BaiduOpenApiHost + BaiduOAuthPath

# error jsons
NoRetryErrorCode = 31062
RetryErrorCode = 150

# about the class
AppID = 'bypyoauth'
AuthPath = '/auth'
RefreshPath = '/refresh'

# logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logStreamHandler = logging.StreamHandler()
logStreamHandler.setLevel(logging.DEBUG)
logger.addHandler(logStreamHandler)

# utils
def inc_list_size(li, size = 3, filler = 0):
	i = len(li)
	while i < size:
		li.append(filler)
		i += 1

def comp_semver(v1, v2):
	v1a = v1.split('.')
	v2a = v2.split('.')
	v1ia = [int(i) for i in v1a]
	v2ia = [int(i) for i in v2a]
	inc_list_size(v1ia, 3)
	inc_list_size(v2ia, 3)
	i = 0
	while i < 3:
		if v1ia[i] != v2ia[i]:
			return v1ia[i] - v2ia[i]
		i += 1
	return 0


def gen_no_retry_json(msg):
	return {'error_code': NoRetryErrorCode,
			'error_msg': msg}

def gen_retry_json(msg):
	return {'error_code': RetryErrorCode,
			'error_msg': msg}

@route('/')
def index():
	response.content_type = 'text/plain'
	return AppID + "\nUpdated: {}\n".format(time.ctime(os.path.getmtime(__file__)))

def need_update_bypy():
	minver = '1.7.8'
	err_json_const = gen_no_retry_json(
		"need to update bypy to at least v{} (pip install -U bypy)".format(minver))
	err_json = {}
	verkey = 'bypy_version'
	if verkey not in request.query:
		err_json = err_json_const
	else:
		bypyver = request.query[verkey]
		if comp_semver(bypyver, minver) < 0:
			err_json = err_json_const
	return err_json

@route(AuthPath)
def auth():
	update_json = need_update_bypy()
	if update_json:
		response.status = 400
		return update_json

	if 'refresh_token' in request.query and 'code' not in request.query:
		err_text = '/auth called for /refresh'
		logger.warning(err_text)
		response.status = 400
		return gen_no_retry_json(err_text)
	error = request.query.error
	code = request.query.code
	redirect_uri = request.query.redirect_uri
	if error:
		err_text = "Error: You DIDN'T authorize.\nError: {}".format(error)
		response.status = 400
		return gen_no_retry_json(err_text)
	elif code:
		try:
			params = {
				'grant_type' : 'authorization_code',
				'code' : code,
				'client_id' : ApiKey,
				'client_secret' : SecretKey,
				# 'redirect_uri' : redirect_uri if redirect_uri else AuthUrl
				'redirect_uri' : redirect_uri if redirect_uri else 'oob'
			}
			if IsPy2:
				pars = ulp.urlencode(params)
			else:
				pars = ulp.urlencode(params)
			url = BaiduOAuthUrl + '?' + pars
			logger.info("POST " + url)
			req = ulr.Request(url = url, method = 'POST')
			resp = ulr.urlopen(req)
			status = resp.getcode()
			resp_text = resp.read()
			response.content_type = 'application/json'
			return resp_text
		except ule.HTTPError as e:
			status = e.code
			resp_text = e.read()
			err_text = "ERROR: Auth failed, please retry.\n" + \
				"HTTP status code: {}\n".format(status) + \
				"Details: Baidu returned:\n{}".format(resp_text)
			logger.warning(err_text)
			response.status = status
			return gen_retry_json(err_text)
	else:
		err_text = "ERROR: Invalid request: 'code' not inside the request.\n" + \
			"Request:\n{}".format(request)
		response.status = 400
		logger.warning(err_text)
		return gen_no_retry_json(err_text)

@route(RefreshPath)
def refresh():
	update_json = need_update_bypy()
	if update_json:
		response.status = 400
		return update_json

	refresh_token = request.query.refresh_token
	#scope = request.query.scope
	if refresh_token:
		try:
			params = {
				'grant_type' : 'refresh_token',
				'refresh_token' : refresh_token,
				'client_id' : ApiKey,
				'client_secret' : SecretKey
				#'scope' : scope if scope else 'basic netdisk'
			}
			if IsPy2:
				pars = ulp.urlencode(params)
			else:
				pars = ulp.urlencode(params)
			url = BaiduOAuthUrl + '?' + pars
			logger.info("POST " + url)
			req = ulr.Request(url = url, method = 'POST')
			resp = ulr.urlopen(req)
			status = resp.getcode()
			resp_text = resp.read()
			response.content_type = 'application/json'
			return resp_text
		except ule.HTTPError as e:
			status = e.code
			resp_text = e.read()
			err_text = "ERROR: Token refreshing failed, please retry.\n" + \
				"HTTP status code: {}\n".format(status) + \
				"Details: Baidu returned:\n{}".format(resp_text)
			logger.warning(err_text)
			response.status = status
			return gen_retry_json(err_text)
	else:
		err_rsp = "Error: param 'refresh_token' not found in your request.\n" + \
			"Request:\n{}".format(request)
		logger.warning(err_rsp)
		response.status = 400
		return gen_no_retry_json(err_rsp)

app = default_app()

if __name__ == "__main__":
	host = '0.0.0.0'
	port = 8080
	if 'PORT' in os.environ:
		port = os.environ['PORT']
	if 'IP' in os.environ:
		host = os.environ['IP']

	run(server='gunicorn', host=host, port=port)

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix

