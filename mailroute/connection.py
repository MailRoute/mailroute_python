# -*- coding: utf-8 -*-
import json
import requests
import urllib
import urlparse

class UnsupportedVersion(Exception):
    pass

class AnswerError(Exception):
    pass

class AuthorizationError(Exception):
    pass

class CanNotInitSchema(Exception):

    def __init__(self, nested_error):
        self._nested = nested_error

    def __str__(self):
        return repr(self._nested)


class InternalError(AnswerError):
    pass

class NotFound(AnswerError):
    pass

class StrangeAnswer(AnswerError):
    pass

class Resource(object):

    def __init__(self, connection, path):
        self.path = path
        self._conn = connection

    def _send(self, full_path, data):
        # TODO
        res = requests.post(full_path, headers=self._conn._auth_header, data=json.dumps(data))
        res.raise_for_status()
        return res.json()

    def _update(self, data):
        res = requests.put(self.path, headers=self._conn._auth_header, data=json.dumps(data))
        res.raise_for_status()
        return res.json()

    def get(self, **opts):
        res = requests.get(self.path, headers=self._conn._auth_header, params=opts)
        if 200 <= res.status_code <= 299:
            return res.json()
        else:
            if 400 <= res.status_code <= 499:
                if res.status_code == 401:
                    raise AuthorizationError, res.url
                raise NotFound, res.url
            elif 500 <= res.status_code <= 599:
                raise InternalError, (res.status_code, res.reason or 'Unknown reason', res.url)
            else:
                raise StrangeAnswer, (res, res.url)

    def one(self, id):
        # TODO: don't allow to use this feature everywhere
        return Resource(self._conn, urlparse.urljoin(self.path, '/{0}/'.format(id)))

    def create(self, data):
        res = requests.post(self.path, headers=self._conn._auth_header, data=json.dumps(data))
        res.raise_for_status()
        return res.json()

    def delete(self):
        res = requests.delete(self.path, headers=self._conn._auth_header)
        res.raise_for_status()

    def update(self, data):
        res = requests.put(self.path, headers=self._conn._auth_header, data=json.dumps(data))
        res.raise_for_status()
        return res.json()

class ConnectionV1(object):

    SERVER_URL = 'https://admin.mailroute.net'

    def __init__(self, username, apikey, server=None):
        self._username = username
        self._apikey = apikey
        if server is not None:
            self.SERVER_URL = server
        self._schemas = {}
        self._s_classes = {}
        self.schema_resource = self.api_resource('/')
        self._init_schemas()

    @property
    def _auth_header(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'ApiKey {login}:{key}'.format(login=self._username, key=self._apikey),
        }

    def _server(self, path):
        return urlparse.urljoin(self.SERVER_URL, path)

    def resource(self, path):
        return Resource(self, self._server(path))

    def api_resource(self, path):
        return Resource(self, self._server('/api/v1{0}'.format(path)))

    def objects(self, e_name):
        return self.api_resource('/{0}/'.format(e_name))

    def _init_schemas(self):
        try:
            self._s_classes = self.schema_resource.get()
        except AnswerError, e:
            raise CanNotInitSchema, e

    def schema_for(self, cname):
        if cname in self._schemas:
            return self._schemas[cname]
        else:
            try:
                descr = self._s_classes[cname]
                schema_path = descr['schema']

                self._schemas[cname] = {'list_endpoint': descr['list_endpoint']}
                self._schemas[cname]['schema'] = self.resource(schema_path).get()

                return self._schemas[cname]
            except (AnswerError, KeyError), e:
                raise CanNotInitSchema, e


_default_connection = None

_connectors_by_version = {
    1: ConnectionV1,
}

def get_default_connection():
    return _default_connection

def configure(username, apikey, server=None, version=1):
    global _default_connection

    if version not in _connectors_by_version:
        raise UnsupportedVersion, version
    ConnectorClass = _connectors_by_version[version]
    _default_connection = ConnectorClass(username, apikey, server=server)
