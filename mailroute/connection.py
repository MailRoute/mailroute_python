# -*- coding: utf-8 -*-
import requests
import urlparse

class UnsupportedVersion(Exception):
    pass

class AnswerError(Exception):
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

    def _grab(self, full_path):
        res = requests.get(full_path, headers=self._auth_header)
        if 200 <= res.status_code <= 299:
            return res.json()
        else:
            if 400 <= res.status_code <= 499:
                raise NotFound, full_path
            elif 500 <= res.status_code <= 599:
                raise InternalError, res.reason or 'Unknown reason'
            else:
                raise StrangeAnswer, res

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
