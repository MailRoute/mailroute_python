# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, VirtualOneToMany

__all__ = ['Domain',]

class Domain(QuerySet):
    class DomainEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'domain'

        active = SmartField()
        bounce_unlisted = SmartField()
        contacts = OneToMany(to_collection='resources.contacts.ContactDomain')
        customer = ForeignField(to_collection='resources.customer.Customer', back_to='domains')
        deliveryport = SmartField()
        domain_aliases = OneToMany(to_collection='resources.domain_alias.DomainAlias')
        email_accounts = OneToMany(to_collection='resources.email_account.EmailAccount')
        hold_email = SmartField()
        name = SmartField()
        mail_servers = OneToMany(to_collection='resources.mail_server.MailServer')
        notification_task = OneToOne(to_collection='resources.notification_task.NotificationDomainTask')
        outbound_enabled = SmartField()
        outbound_servers = OneToMany(to_collection='resources.outbound_server.OutboundServer')
        policy = OneToOne(to_collection='resources.policy.PolicyDomain')
        outbound_enabled = SmartField()

    Entity = DomainEntity

    def get_quaranine(self):
        pass

    def move_to_customer(self, target_customer):
        self.customer = target_customer
        self.save()

    def create_contact(self, params):
        return self.contacts.create(domain=self, **params)

    def create_mailserver(self, params):
        return self.mail_servers.create(domain=self, **params)

    def create_outbound_server(self, params_or_ip):
        if isinstance(params_or_ip, basestring):
            ip = params_or_ip
            return self.outbound_servers.create({'server': ip, 'domain': self})
        else:
            params = params_or_ip
            return self.mail_servers.create(domain=self, **params)

    def create_email_account(self, params):
        return self.email_accounts.create(domain=self, **params)

    def bulk_create_email_account(self, params_list):
        for params in params_list:
            self.create_email_account(params)

    def create_alias(self, params):
        return self.domain_aliases.create(domain=self, **params)

    def add_to_blacklist(self, email):
        pass

    def add_to_whitelist(self, email):
        pass
