# -*- coding: utf-8 -*-
import sure
import json
import uuid
import unittest
import mailroute
import httpretty

class TestCustomMethods(unittest.TestCase):

    ACCESS_USER = ('test_python', 'e7b46a7392629c144ee8237454b7888a30f93e69')

    def setUp(self):
        mailroute.configure(*self.ACCESS_USER, server='https://ci.mailroute.net')

    def tearDown(self):
        httpretty.HTTPretty.disable()   # if some test function fails force disabling anyway

    def test_contacts(self):
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        res_obj = mailroute.Reseller.create(name=new_name)
        res_obj.create_contact({
            'email': '{0}@test-mail.com'.format(prefix),
            'first_name': prefix
        })
        (contact1,) = mailroute.ContactReseller.filter(email='{0}@test-mail.com'.format(prefix))
        contact1.first_name.should.be.equal(prefix)
        (contact2,) = res_obj.contacts
        contact1.should.be.equal(contact2)

        len(res_obj.contacts.filter(first_name='Unknown')).should.be.equal(0)
        new_one.delete()

    def test_new_admin(self):
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        res_obj = mailroute.Reseller.create(name=new_name)

        ad_mail = '{0}@admin-mail.com'.format(prefix)
        new_admin = res_obj.create_admin(ad_mail, send_welcome=True)
        new_admin.email.should.be.equal(ad_mail)
        new_admin.send_welcome.should.be.true
        new_admin.id.should_not.be.none

        (found_admin,) = mailroute.Admins.filter(email=ad_mail).fetch()
        found_admin.should.be.equal(new_admin)

        res_obj.delete_admin(ad_mail)
