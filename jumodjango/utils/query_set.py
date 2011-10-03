from django.db import models

class QuerySet(models.query.QuerySet):
    @classmethod
    def as_manager(cls):
        class QuerySetManager(models.Manager):
            use_for_related_fields = True

            def __init__(self):
                super(QuerySetManager, self).__init__()
                self.queryset_class = cls

            def get_query_set(self):
                return self.queryset_class(self.model)

            def __getattr__(self, attr, *args):
                try:
                    return getattr(self.__class__, attr, *args)
                except AttributeError:
                    return getattr(self.get_query_set(), attr, *args)

        return QuerySetManager()
