# -*- coding: utf-8 -*-
import sure
import json
import unittest
import mailroute
import httpretty
from tests import base

class TestSchema(base.Test):

    @property
    def entity_classes(self):
        return [
            mailroute.Admin,
            mailroute.Branding,
            mailroute.ContactCustomer,
            mailroute.ContactDomain,
            mailroute.ContactEmailAccount,
            mailroute.ContactReseller,
            mailroute.Customer,
            mailroute.Domain,
            mailroute.DomainAlias,
            mailroute.DomainWithAlias,
            mailroute.EmailAccount,
            mailroute.LocalPartAlias,
            mailroute.MailServer,
            mailroute.NotificationAccountTask,
            mailroute.NotificationDomainTask,
            mailroute.OutboundServer,
            mailroute.PolicyDomain,
            mailroute.PolicyUser,
            mailroute.Reseller,
            mailroute.WBList,
        ]

    @httpretty.httprettified
    def test_wrong_schema(self):
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, 'https://ci.mailroute.net/api/v1/',
                                         status=200, body=json.dumps({}),
                                         content_type='application/json')
        mailroute.configure(*self.ACCESS_USER, server='https://ci.mailroute.net')

        for QClass in self.entity_classes:
            QClass.Entity.schema.when.called_with().should.throw(mailroute.CanNotInitSchema)

    def test_all_entities(self):
        mailroute.configure(*self.ACCESS_USER, server='https://ci.mailroute.net')

        for QClass in self.entity_classes:
            QClass.Entity.schema().should_not.be.empty
            print QClass
            QClass.Entity.is_actual().should.be.true

if __name__ == '__main__':
    unittest.main()
