# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, InvalidValue

__all__ = ['CommonContactMixin', 'ContactCustomer', 'ContactDomain', 'ContactEmailAccount', 'ContactReseller',]

class TooLongError(InvalidValue):
    pass

class MaxField(SmartField):

    def __init__(self, *args, **kwargs):
        self.max_length = kwargs.pop('length', 0)
        self._another_validator = kwargs.pop('validator', 0)
        super(MaxField, self).__init__(validator=self.check_max_length, *args, **kwargs)

    def check_max_length(self, vtype, value):
        if len(value) > self.max_length:
            raise TooLongError, 'Maximal allowed length is {} but value has {}'.format(self.max_length, len(value))
        if self._another_validator:
            self._another_validator(vtype, value)

class CommonContactMixin(AbstractDocument):
    MAX_NAME_LENGTH = 30

    address = SmartField()
    address2 = SmartField()
    city = SmartField()
    country = SmartField()
    email = SmartField(required=True)
    first_name = MaxField(length=MAX_NAME_LENGTH)
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

        customer = ForeignField(to_collection='resources.Customer', related_name='contacts')

class ContactDomain(QuerySet):
    class ContactDomainEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_domain'

        domain = ForeignField(to_collection='resources.domain.Domain', related_name='contacts')

class ContactEmailAccount(QuerySet):
    class ContactEmailAccountEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_email_account'

        email_account = OneToOne(to_collection='resources.email_acount.EmailAccount')

class ContactReseller(QuerySet):
    class ContactResellerEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_reseller'

        reseller = ForeignField(to_collection='resources.reseller.Reseller', related_name='contacts')
