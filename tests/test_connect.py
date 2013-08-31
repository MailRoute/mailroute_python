# -*- coding: utf-8 -*-
import sure
import json
import unittest
import mailroute
import httpretty
from tests import base

class TestConnection(base.Test):

    def test_wrong_auth(self):
        mailroute.configure('invalid_user', 'wrong_key', server='https://ci.mailroute.net')
        mailroute.get_default_connection().schema_for.when.called_with('domain').should \
            .throw(mailroute.AuthorizationError)

    @httpretty.httprettified
    def test_internal_error(self):
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, 'https://ci.mailroute.net/api/v1/',
                                         status=500, body=json.dumps({'error': 'Test error'}),
                                         content_type='application/json')
        mailroute.configure.when.called_with(*self.ACCESS_USER, server='https://ci.mailroute.net').should \
                .throw(mailroute.CanNotInitSchema)

    @httpretty.httprettified
    def test_init_issue(self):
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, 'https://ci.mailroute.net/api/v1/',
                                         status=404, body=json.dumps({'error': 'Test error'}),
                                         content_type='application/json')
        mailroute.configure.when.called_with(*self.ACCESS_USER, server='https://ci.mailroute.net').should \
                .throw(mailroute.CanNotInitSchema)

    def test_correct_auth(self):
        mailroute.configure(*self.ACCESS_USER, server='https://ci.mailroute.net')
        mailroute.get_default_connection().should_not.be.none

    def test_unsupported_version(self):
        mailroute.configure.when.called_with('user', 'some_correct_key', version=-1).should \
                .throw(mailroute.UnsupportedVersion)


if __name__ == '__main__':
    unittest.main()
