import settings
# Data science toolkit homes
from dstk import DSTK

#from gevent import monkey
#monkey.patch_all()

dstk = DSTK({'apiBase': settings.DSTK_API_BASE, 'checkVersion': False})