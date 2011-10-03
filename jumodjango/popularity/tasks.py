'''
Created on Apr 28, 2011

@author: al
'''

from celery.task import Task
from contextlib import contextmanager
from django.core.cache import cache
from django.db import connections
from users.models import User
from issue.models import Issue
from org.models import Org
from collections import namedtuple
from popularity.models import TopList, TopListItem

LOCK_EXPIRE = 60*5

class TaskLockedException(Exception):
    pass

class BasePopularity(Task):
    name = None

    @property
    def cache_key(self):
        if self.name is None:
            raise Exception('Name your tasks fooool!')
        return '%s-lock' % self.name

    @contextmanager
    def task_lock(self):
        try:
            cache.add(self.cache_key, 'true', LOCK_EXPIRE)
            yield
        except Exception:
            raise TaskLockedException('This task is already locked')
        finally:
            cache.delete(self.cache_key)

    def get_items_for_list(self, limit):
        raise NotImplementedError('Children need to implement their own')

    def update_list(self, items):
        pass

    def run(self):
        with self.task_lock():
            # Do stuff
            items = self.get_items_for_list()
            self.update_list(items)

class OrgPopularity(BasePopularity):
    name = 'org.popularity'
    list_type_id = 2

    def get_items_for_list(self, limit):
        return Issue.objects.raw("""
        select o.id
        from org_org o
        join org_usertoorgfollow uo
          on uo.org_id = o.id
          and uo.following=1
        group by o.id
        order by count(*) desc
        limit %(limit)s
        """, {'limit': limit})


class IssuePopularity(BasePopularity):
    name = 'issue.popularity'
    list_type_id = 3

    def get_items_for_list(self, limit):
        return Issue.objects.raw("""
        select i.id
        from issue_issue i
        join issue_usertoissuefollow ui
          on ui.issue_id = i.id
          and ui.following=1
        group by i.id
        order by count(*) desc
        limit %(limit)s
        """, {'limit': limit})
