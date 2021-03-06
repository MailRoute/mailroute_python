# -*- coding: utf-8 -*-
import json
import requests
import urllib
import urlparse

class NoConnectionProvided(Exception):
    pass

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

class FinalResource(AnswerError):
    pass

class CreateError(AnswerError):
    pass

class UpdateError(AnswerError):
    pass

class DocJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__serialize__'):
            converter = getattr(o, '__serialize__')
            return converter()
        return super(DocJSONEncoder, self).default(o)

class Resource(object):

    def __init__(self, path, final=False, auth=None):
        self.path = path
        self._auth = auth if auth is not None else {}
        self._final = final
        self._dumper = DocJSONEncoder()

    def _handle_error(self, error, Error4xx):
        res = error.response
        try:
            description = res.json()
        except:
            description = {}

        if 400 <= res.status_code <= 499:
            if res.status_code == 401:
                raise AuthorizationError, (res.url, description)
            raise Error4xx, (res.url, description)
        elif 500 <= res.status_code <= 599:
            raise InternalError, (res.status_code, res.reason or 'Unknown reason',
                                  res.url, description)
        else:
            raise StrangeAnswer, (res, res.url, description)

    def get(self, **opts):
        try:
            res = requests.get(self.path, params=opts, headers=self._auth)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError, e:
            self._handle_error(e, NotFound)

    def one(self, id):
        if not self._final:
            return Resource(urlparse.urljoin(self.path, '{0}/'.format(id)), auth=self._auth, final=True)
        else:
            raise FinalResource, self.path

    def call(self, method):
        return Resource(urlparse.urljoin(self.path, '{0}/'.format(method)), auth=self._auth, final=self._final)

    def sub(self, *elements):
        if not self._final:
            elements = map(str, elements) + ['']
            return Resource(urlparse.urljoin(self.path, '/'.join(elements)), auth=self._auth)
        else:
            raise FinalResource, self.path

    def create(self, data):
        try:
            res = requests.post(self.path, data=self._dumper.encode(data), headers=self._auth)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError, e:
            self._handle_error(e, CreateError)

    def delete(self):
        try:
            res = requests.delete(self.path, headers=self._auth)
            res.raise_for_status()
            return True
        except requests.exceptions.HTTPError, e:
            self._handle_error(e, NotFound)

    def update(self, data):
        try:
            res = requests.put(self.path, data=self._dumper.encode(data), headers=self._auth)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError, e:
            self._handle_error(e, UpdateError)

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
        return Resource(self._server(path), final=True, auth=self._auth_header)

    def api_resource(self, path):
        if not path.startswith('/'):
            path = '/' + path
        return Resource(self._server('/api/v1{0}'.format(path)), auth=self._auth_header)

    def objects(self, e_name):
        assert '/' not in e_name, 'Name should not contain slashes'
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
    if _default_connection is not None:
        return _default_connection
    else:
        raise NoConnectionProvided

def configure(username, apikey, server=None, version=1):
    global _default_connection

    if version not in _connectors_by_version:
        raise UnsupportedVersion, version
    ConnectorClass = _connectors_by_version[version]
    _default_connection = ConnectorClass(username, apikey, server=server)
