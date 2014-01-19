# -*- coding: utf-8 -*-
import unittest
import httpretty
import mailroute

class Test(unittest.TestCase):

    ACCESS_USER = ('test_python', 'e7b46a7392629c144ee8237454b7888a30f93e69')

class AccessTest(Test):

    def setUp(self):
        mailroute.configure(*self.ACCESS_USER, server='https://ci.mailroute.net')

    def tearDown(self):
        httpretty.HTTPretty.disable()   # if some test function fails force disabling anyway
