# -*- coding: utf-8 -*-
import sure
import json
import unittest
import mailroute
import httpretty

class TestConnection(unittest.TestCase):

    ACCESS_USER = ('test_python', 'e7b46a7392629c144ee8237454b7888a30f93e69')

    def test_wrong_auth(self):
        mailroute.configure.when.called_with('invalid_user', 'wrong_key').should \
                .throw(mailroute.AuthorizationError)

    @httpretty.httprettified
    def test_internal_error(self):
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, 'https://ci.mailroute.net/api/v1/',
                                         status=500, body=json.dumps({'error': 'Test error'}),
                                         content_type='application/json')
        mailroute.configure.when.called_with(*self.ACCESS_USER, server='https://ci.mailroute.net').should \
                .throw(mailroute.CanNotInitSchema, \
                       'InternalError(500, \'Internal Server Error\', \'https://ci.mailroute.net/api/v1/\')')

    @httpretty.httprettified
    def test_init_issue(self):
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, 'https://ci.mailroute.net/api/v1/',
                                         status=404, body=json.dumps({'error': 'Test error'}),
                                         content_type='application/json')
        mailroute.configure.when.called_with(*self.ACCESS_USER, server='https://ci.mailroute.net').should \
                .throw(mailroute.CanNotInitSchema, \
                       'NotFound(\'https://ci.mailroute.net/api/v1/\',)')

    def test_correct_auth(self):
        mailroute.configure(*self.ACCESS_USER, server='https://ci.mailroute.net')
        mailroute.get_default_connection().should_not.be.empty

    def test_unsupported_version(self):
        mailroute.configure.when.called_with('user', 'some_correct_key', version=-1).should \
                .throw(mailroute.UnsupportedVersion)


if __name__ == '__main__':
    unittest.main()
