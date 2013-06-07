# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, VirtualOneToMany

__all__ = ['EmailAccount',]

class EmailAccount(QuerySet):
    class EmailAccountEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'email_account'

        change_pwd = SmartField()
        confirm_password = SmartField()
        contact = OneToOne(to_collection='resources.contact.Contact')
        create_opt = SmartField()
        domain = ForeignField(to_collection='resources.domain.Domain', back_to='email_accounts')
        localpart = SmartField()
        localpart_aliases = OneToMany(to_collection='resources.localpart_alias.LocalPartAlias')
        notification_task = OneToOne(to_collection='resources.notification_task.NotificationAccountTask')
        password = SmartField()
        policy = OneToOne(to_collection='resources.policy.PolicyUser')
        priority = SmartField()
        send_welcome = SmartField()
        wblist = OneToMany(to_collection='resources.wblist.WBList')

    Entity = EmailAccountEntity

    def add_alias(local_part):
        self.localpart_aliases.create(email_account=self, local_part=local_part)

    @classmethod
    def create(cls, *args, **initial):
        if len(args) == 1 and isinstance(args[0], basestring):
            localpart, domain_name = args[0].split('@')
            DomainClass = cls.Entity.domain.find_class(cls)
            domain = DomainClass.get(name=domain_name)

            return super(EmailAccount, cls).create(**{
                'localpart': localpart,
                'domain': domain,
            })
        else:
            return super(EmailAccount, cls).create(**initial)

    def add_to_blacklist(self, address):
        self.wblist.create(wb='b', mail_address=address, email_account=self)

    def add_to_whitelist(self, address):
        self.wblist.create(wb='w', mail_address=address, email_account=self)

    def set_password(self, new_pass):
        self.password = new_pass
        self.save()
