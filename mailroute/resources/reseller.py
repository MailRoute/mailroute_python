# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['Reseller',]

class Reseller(QuerySet):
    class ResellerEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'reseller'

        name = SmartField(required=True)
        allow_customer_branding = SmartField()
        allow_branding = SmartField()
        branding_info = OneToOne(to_collection='resources.branding_info.Branding')
        contacts = OneToMany(to_collection='resources.contacts.ContactReseller')
        customers = OneToMany(to_collection='resources.customer.Customer')
        admins = OneToMany(to_collection='resources.admins.Admin')

        def create_admin(self, email, send_welcome):
            return self.admins.create(email=email, send_welcome=send_welcome)

        def delete_admin(self, email):
            (admin_obj,) = self.admins.filter(email=email)
            return admin_obj.delete()

        def create_contact(self, params):
            return self.contacts.create(reseller=self, **params)

        def create_customer(self, params):
            return self.customers.create(reseller=self, **params)

    Entity = ResellerEntity
