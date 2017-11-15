from __future__ import absolute_import
from collections import defaultdict
from corehq.apps.reminders.models import CaseReminderHandler, METHOD_IVR_SURVEY
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, **options):
        handlers = CaseReminderHandler.view(
            'reminders/handlers_by_domain_case_type',
            include_docs=True
        ).all()

        active_ivr_handlers = defaultdict(lambda: 0)
        inactive_ivr_handlers = defaultdict(lambda: 0)

        for handler in handlers:
            if handler.method == METHOD_IVR_SURVEY:
                if handler.active:
                    active_ivr_handlers[handler.domain] += 1
                else:
                    inactive_ivr_handlers[handler.domain] += 1

        print("============ Inactive IVR Handlers ============")
        for domain, count in inactive_ivr_handlers.items():
            print("%s: %s" % (domain, count))

        print("============ Active IVR Handlers ============")
        for domain, count in active_ivr_handlers.items():
            print("%s: %s" % (domain, count))
