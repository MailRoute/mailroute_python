# -*- coding: utf-8 -*-
import logic
from queryset import QuerySet
from document import BaseDocument, AbstractDocument, BaseCreatableDocument
from fields import SmartField, OneToMany, OneToOne, ForeignField

class Branding(QuerySet):
    class BrandingEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'brandinginfo'

        color = SmartField()
        customer = OneToOne(to_collection='Customer')
        domain = SmartField()
        email_from = SmartField()
        enabled = SmartField()
        favicon = SmartField()
        highlight_color = SmartField()
        logo = SmartField()
        reseller = OneToOne(to_collection='Reseller')
        service_name = SmartField()
        ssl_cert_passphrase = SmartField()
        subdomain = SmartField()
        contact_us_url = SmartField()
        page_color = SmartField()

    Entity = BrandingEntity


class Reseller(QuerySet):
    class ResellerEntity(BaseCreatableDocument, logic.ResellerMixin):
        class Meta:
            entity_name = 'reseller'

        name = SmartField(required=True)
        allow_customer_branding = SmartField()
        allow_branding = SmartField()
        branding_info = OneToOne(to_collection='Branding')
        contacts = OneToMany(to_collection='ContactReseller')
        customers = OneToMany(to_collection='Customer')
        admins = OneToMany(to_collection='Admins')

    Entity = ResellerEntity

class Admins(QuerySet):
    class AdminsEntity(BaseDocument):
        class Meta:
            entity_name = 'admins'

        date_joined = SmartField()
        email = SmartField()
        is_active = SmartField()
        last_login = SmartField()
        send_welcome = SmartField()
        username = SmartField()
        reseller = ForeignField(to_collection='Reseller', back_to='admins')
        customer = ForeignField(to_collection='Customer', back_to='admins')

    Entity = AdminsEntity

class CommonContactMixin(AbstractDocument):
    address = SmartField()
    address2 = SmartField()
    city = SmartField()
    country = SmartField()
    email = SmartField()
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

        customer = ForeignField(to_collection='Customer', back_to='contacts')

    Entity = ContactCustomerEntity

class ContactDomain(QuerySet):
    class ContactDomainEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_domain'

        domain = ForeignField(to_collection='Domain', back_to='contacts')

    Entity = ContactDomainEntity

class ContactEmailAccount(QuerySet):
    class ContactEmailAccountEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_email_account'

        email_account = OneToOne(to_collection='EmailAccount')

    Entity = ContactEmailAccountEntity

class ContactReseller(QuerySet):
    class ContactResellerEntity(BaseCreatableDocument, CommonContactMixin):
        class Meta:
            entity_name = 'contact_reseller'

        reseller = ForeignField(to_collection='Reseller', back_to='contacts')

    Entity = ContactResellerEntity

class Customer(QuerySet):
    class CustomerEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'customer'

        name = SmartField(required=True)
        allow_branding = SmartField()
        branding_info = OneToOne(to_collection='Branding')
        is_full_user_list = SmartField()
        reported_user_count = SmartField()
        reseller = ForeignField(to_collection='Reseller', back_to='customers')
        contacts = OneToMany(to_collection='ContactCustomer')
        domains = OneToMany(to_collection='Domain')
        admins = OneToMany(to_collection='Admins')

    Entity = CustomerEntity

class Domain(QuerySet):
    class DomainEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'domain'

        active = SmartField()
        bounce_unlisted = SmartField()
        contacts = OneToMany(to_collection='ContactDomain')
        customer = ForeignField(to_collection='Customer', back_to='domains')
        deliveryport = SmartField()
        domain_aliases = OneToMany(to_collection='DomainAlias')
        email_accounts = OneToMany(to_collection='EmailAccount')
        hold_email = SmartField()
        name = SmartField()
        mail_servers = OneToMany(to_collection='MailServer')
        notification_task = OneToOne(to_collection='NotificationDomainTask')
        outbound_enabled = SmartField()
        outbound_servers = OneToMany(to_collection='OutboundServer')
        policy = OneToOne(to_collection='PolicyDomain')
        outbound_enabled = SmartField()

    Entity = DomainEntity

class DomainAlias(QuerySet):
    class DomainAliasEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'domain_alias'

        active = SmartField()
        domain = ForeignField(to_collection='Domain', back_to='domain_aliases')
        name = SmartField()

    Entity = DomainAliasEntity

class DomainWithAlias(QuerySet):
    class DomainWithAliasEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'domain_with_alias'

        domain = OneToOne(to_collection='Domain')
        name = SmartField()
        type = SmartField()

    Entity = DomainWithAliasEntity

class EmailAccount(QuerySet):
    class EmailAccountEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'email_account'

        change_pwd = SmartField()
        confirm_password = SmartField()
        contact = OneToOne(to_collection='Contact')
        create_opt = SmartField()
        domain = ForeignField(to_collection='Domain', back_to='email_accounts')
        localpart = SmartField()
        localpart_aliases = OneToMany(to_collection='LocalPartAlias')
        notification_task = OneToOne(to_collection='NotificationAccountTask')
        password = SmartField()
        policy = OneToOne(to_collection='PolicyUser')
        priority = SmartField()
        send_welcome = SmartField()

    Entity = EmailAccountEntity

class LocalPartAlias(QuerySet):
    class LocalPartAliasEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'localpart_alias'

        domain = OneToOne(to_collection='Domain')
        email_account = ForeignField(to_collection='EmailAccount', back_to='localpart_aliases')
        localpart = SmartField()
        type = SmartField()

    Entity = LocalPartAliasEntity

class MailServer(QuerySet):
    class MailServerEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'mail_server'

        domain = ForeignField(to_collection='Domain', back_to='mail_servers')
        priority = SmartField()
        sasl_login = SmartField()
        sasl_password = SmartField()
        server = SmartField()
        use_sasl = SmartField()

    Entity = MailServerEntity

class NotificationAccountTask(QuerySet):
    class NotificationAccountTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_account_task'

        email_account = OneToOne(to_collection='EmailAccount')
        enabled = SmartField()
        priority = SmartField()

    Entity = NotificationAccountTaskEntity

class NotificationDomainTask(QuerySet):
    class NotificationDomainTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_domain_task'

        domain = OneToOne(to_collection='Domain')
        enabled = SmartField()
        priority = SmartField()

    Entity = NotificationDomainTaskEntity

class OutboundServer(QuerySet):
    class OutboundServerEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'outbound_server'

        domain = ForeignField(to_collection='Domain', back_to='outbound_servers')
        server = SmartField()

    Entity = OutboundServerEntity

class CommonPolicyMixin(AbstractDocument):
    addr_extension_bad_header = SmartField()
    addr_extension_banned = SmartField()
    addr_extension_spam = SmartField()
    addr_extension_virus = SmartField()
    archive_quarantine_to = SmartField()
    bad_header_lover = SmartField()
    bad_header_quarantine_to = SmartField()
    banned_files_lover = SmartField()
    banned_quarantine_to = SmartField()
    bypass_banned_checks = SmartField()
    bypass_header_checks = SmartField()
    bypass_spam_checks = SmartField()
    bypass_virus_checks = SmartField()
    message_size_limit = SmartField()
    priority = SmartField()
    spam_kill_level = SmartField()
    spam_lover = SmartField()
    spam_quarantine_cutoff_level = SmartField()
    spam_quarantine_to = SmartField()
    spam_subject_tag = SmartField()
    spam_subject_tag2 = SmartField()
    spam_subject_tag3 = SmartField()
    spam_tag2_level = SmartField()
    spam_tag3_level = SmartField()
    spam_tag_level = SmartField()
    unchecked_lover = SmartField()
    unchecked_quarantine_to = SmartField()
    virus_lover = SmartField()
    virus_quarantine_to = SmartField()
    warnbadhrecip = SmartField()
    warnbannedrecip = SmartField()
    warnvirusrecip = SmartField()

class PolicyDomain(QuerySet):
    class PolicyDomainEntity(BaseDocument, CommonPolicyMixin):
        class Meta:
            entity_name = 'policy_domain'

        domain = OneToOne(to_collection='Domain')

    Entity = PolicyDomainEntity

class PolicyUser(QuerySet):
    class PolicyUserEntity(BaseDocument, CommonPolicyMixin):
        class Meta:
            entity_name = 'policy_user'

        email_account = OneToOne(to_collection='EmailAccount')

    Entity = PolicyUserEntity

__all__ = ['Branding', 'Reseller', 'Admins', 'ContactCustomer', 'ContactDomain', 'ContactEmailAccount',
           'ContactReseller', 'Customer', 'Domain', 'DomainAlias', 'DomainWithAlias', 'EmailAccount',
           'LocalPartAlias', 'MailServer', 'NotificationAccountTask', 'NotificationDomainTask',
           'OutboundServer', 'PolicyDomain', 'PolicyUser']
