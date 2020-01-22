from corehq.apps.cleanup.management.commands.populate_sql_model_from_couch_model import PopulateSQLCommand


class Command(PopulateSQLCommand):
    help = """
        Adds a SQLRegistrationRequest for any RegistrationRequest doc that doesn't yet have one.
    """

    @property
    def couch_class(self):
        try:
            from corehq.apps.registration.models import RegistrationRequest
            return RegistrationRequest
        except ImportError:
            return None

    @property
    def couch_class_key(self):
        return set(['activation_guid'])

    @property
    def sql_class(self):
        from corehq.apps.registration.models import SQLRegistrationRequest
        return SQLRegistrationRequest

    def update_or_create_sql_object(self, doc):
        model, created = self.sql_class.objects.get_or_create(
            activation_guid=doc['activation_guid'],
            defaults={
                "tos_confirmed": doc.get("tos_confirmed"),
                "request_time": doc.get("request_time"),
                "request_ip": doc.get("request_ip"),
                "confirm_time": doc.get("confirm_time"),
                "confirm_ip": doc.get("confirm_ip"),
                "domain": doc.get("domain"),
                "new_user_username": doc.get("new_user_username"),
                "requesting_user_username": doc.get("requesting_user_username"),
            })
        return (model, created)
