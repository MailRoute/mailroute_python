# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['CommonPolicyMixin', 'PolicyDomain', 'PolicyUser',]

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

        domain = OneToOne(to_collection='resources.domain.Domain')

    Entity = PolicyDomainEntity

class PolicyUser(QuerySet):
    class PolicyUserEntity(BaseDocument, CommonPolicyMixin):
        class Meta:
            entity_name = 'policy_user'

        email_account = OneToOne(to_collection='resources.email_account.EmailAccount')

    Entity = PolicyUserEntity
