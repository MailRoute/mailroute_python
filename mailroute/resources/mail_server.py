# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['MailServer',]

class MailServer(QuerySet):
    class MailServerEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'mail_server'

        domain = ForeignField(to_collection='resources.domain.Domain', back_to='mail_servers')
        priority = SmartField()
        sasl_login = SmartField()
        sasl_password = SmartField()
        server = SmartField()
        use_sasl = SmartField()

    Entity = MailServerEntity
