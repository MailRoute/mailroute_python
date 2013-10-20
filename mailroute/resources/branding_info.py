# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['Branding',]

class Branding(QuerySet):
    class BrandingEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'brandinginfo'

        color = SmartField()
        customer = OneToOne(to_collection='resources.customer.Customer')
        domain = SmartField()
        email_from = SmartField()
        enabled = SmartField()
        favicon = SmartField()
        highlight_color = SmartField()
        logo = SmartField()
        reseller = OneToOne(to_collection='resources.reseller.Reseller')
        service_name = SmartField()
        ssl_cert_passphrase = SmartField()
        subdomain = SmartField()
        contact_us_url = SmartField()
        page_color = SmartField()
