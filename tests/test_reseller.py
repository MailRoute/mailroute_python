# -*- coding: utf-8 -*-
import sure
import json
import uuid
import unittest
import mailroute
import httpretty
from mailroute.resources import contacts
from mailroute import queryset
from tests import base

class TestCustomMethods(base.AccessTest):

    def test_contacts(self):
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        res_obj = mailroute.Reseller.create(name=new_name)
        max_l = mailroute.ContactCustomer.Entity.MAX_NAME_LENGTH

        too_long_prefix = prefix + ('.' * max(0, max_l - len(prefix) + 1))
        res_obj.create_contact.when.called_with({
            'email': '{0}@test-mail.com'.format(prefix),
            'first_name': prefix
        }).should.throw(contacts.TooLongError)

        cprefix = prefix[:max_l]
        res_obj.create_contact({
            'email': '{0}@test-mail.com'.format(prefix),
            'first_name': cprefix
        })

        (contact1,) = mailroute.ContactReseller.filter(email='{0}@test-mail.com'.format(prefix))
        contact1.first_name.should.be.equal(cprefix)
        (contact2,) = res_obj.contacts

        contact1.should.be.equal(contact2)

        len(res_obj.contacts.filter(email='{0}@Unknown'.format(prefix))).should.be.equal(0)
        res_obj.contacts.filter.when.called_with(first_name='Unknown').should.throw(queryset.InvalidFilter)
        res_obj.delete()

    def test_fresh_admins(self):
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        res_obj = mailroute.Reseller.create(name=new_name)
        list(res_obj.admins).should.be.empty
        res_obj.delete()

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

    def test_branding(self):
        new_one = mailroute.Reseller.create(name=new_name)

        new_one.branding_info.should.be.a(mailroute.Branding.BrandingEntity)
        new_one.branding_info.reseller.should.be.equal(new_one)

        mailroute.Reseller.filter.when.called_with(branding_info__color='red').should. \
            throw(mailroute.InvalidFilter)
