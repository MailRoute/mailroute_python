# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['OutboundServer',]

class OutboundServer(QuerySet):
    class OutboundServerEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'outbound_server'

        domain = ForeignField(to_collection='resources.domain.Domain', back_to='outbound_servers')
        server = SmartField()
