# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, VirtualOneToMany

__all__ = ['CommonContactMixin', 'ContactCustomer', 'ContactDomain', 'ContactEmailAccount', 'ContactReseller',]

class CommonContactMixin(AbstractDocument):
    address = SmartField()
    address2 = SmartField()
    city = SmartField()
    country = SmartField()
    email = SmartField(required=True)
    first_name = SmartField()
    is_billing = SmartField()
    is_emergency = SmartField()
    is_technical = SmartField()
    last_name = SmartField()
    phone = SmartField()
    state = SmartField()
    zipcode = SmartField()

class ContactCustomer(QuerySet):
    class ContactCustomerEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_customer'

        customer = ForeignField(to_collection='resources.Customer', back_to='contacts')

    Entity = ContactCustomerEntity

class ContactDomain(QuerySet):
    class ContactDomainEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_domain'

        domain = ForeignField(to_collection='resources.domain.Domain', back_to='contacts')

    Entity = ContactDomainEntity

class ContactEmailAccount(QuerySet):
    class ContactEmailAccountEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_email_account'

        email_account = OneToOne(to_collection='resources.email_acount.EmailAccount')

    Entity = ContactEmailAccountEntity

class ContactReseller(QuerySet):
    class ContactResellerEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_reseller'

        reseller = ForeignField(to_collection='resources.reseller.Reseller', back_to='contacts')

    Entity = ContactResellerEntity
