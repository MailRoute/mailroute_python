# -*- coding: utf-8 -*-
import json
import requests
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

class ConnectionV1(object):

    SERVER_URL = 'https://admin.mailroute.net'

    def __init__(self, username, apikey):
        self._username = username
        self._apikey = apikey
        self._schemas = {}
        self._s_classes = {}
        self._init_schemas()

    @property
    def _auth_header(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'ApiKey {login}:{key}'.format(login=self._username, key=self._apikey),
        }

    def _server(self, path):
        return urlparse.urljoin(self.SERVER_URL, path)

    def _api(self, path):
        return self._server('/api/v1{0}'.format(path))

    def _object_id(self, e_name, id):
        return self._api('/{0}/{1}/'.format(e_name, id))

    def _objects(self, e_name, **opts):
        # REWORK THIS SHIT!!!
        if opts:
            opts = '?' + '&'.join('{0}={1}'.format(k, v) for k, v in opts.iteritems())
        else:
            opts = ''
        return self._api('/{0}/'.format(e_name) + opts)

    def _send(self, full_path, data):
        # TODO
        res = requests.post(full_path, headers=self._auth_header, data=json.dumps(data))
        res.raise_for_status()
        return res.json()

    def _update(self, full_path, data):
        # TODO
        res = requests.put(full_path, headers=self._auth_header, data=json.dumps(data))
        print full_path, data
        res.raise_for_status()
        return res.json()

    def _remove(self, full_path):
        # TODO
        res = requests.delete(full_path, headers=self._auth_header)
        res.raise_for_status()

    def _grab(self, full_path):
        res = requests.get(full_path, headers=self._auth_header)
        if 200 <= res.status_code <= 299:
            return res.json()
        else:
            if 400 <= res.status_code <= 499:
                if res.status_code == 401:
                    raise AuthorizationError, full_path
                raise NotFound, full_path
            elif 500 <= res.status_code <= 599:
                raise InternalError, (res.status_code, res.reason or 'Unknown reason', full_path)
            else:
                raise StrangeAnswer, (res, full_path)

    def _init_schemas(self):
        try:
            self._s_classes = self._grab(self._api('/'))
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
                self._schemas[cname]['schema'] = self._grab(self._server(schema_path))

                return self._schemas[cname]
            except AnswerError, e:
                raise CanNotInitSchema, e


_default_connection = None

_connectors_by_version = {
    1: ConnectionV1,
}

def configure(username, apikey, version=1):
    global _default_connection

    if version not in _connectors_by_version:
        raise UnsupportedVersion, version
    ConnectorClass = _connectors_by_version[version]
    _default_connection = ConnectorClass(username, apikey)
