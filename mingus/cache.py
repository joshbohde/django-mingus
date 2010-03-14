from basic.blog.models import BlogRoll, Category, Settings, Post
from quoteme.models import Quote
from basic.bookmarks.models import Bookmark
from basic.elsewhere.models import SocialNetworkProfile
from django_proxy.models import Proxy
from flatblocks.models import FlatBlock

from django.dispatch import dispatcher
from django.db.models import signals
from staticgenerator import quick_delete
from django.core.urlresolvers import reverse

from django.core.cache import cache
from django.utils.encoding import force_unicode 
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote

CACHED_TEMPLATES = ['"base.%s"' % s for s in ["navbars", "profiles", "category_list",
              "post_list", "archive", "blogroll", "popular-posts"]]

def gen_template_cache_key(fragment_name):
    args = md5_constructor(u'')
    return 'template.cache.%s.%s' % (fragment_name, args.hexdigest())

def invalidate_base_template_cache():
    for x in (gen_template_cache_key(x) for x in CACHED_TEMPLATES):
        cache.delete(x)

def delete_proxy(sender, instance, **kwargs):
    invalidate_base_template_cache()
    quick_delete(reverse("home_index"),
                 instance.content_object,
                 )

def delete_content(sender, instance, **kwargs):
    invalidate_base_template_cache()
    quick_delete(reverse("home_index"),
                 instance,
                 )

def delete_all(sender, instance, **kwargs):
    invalidate_base_template_cache()
    quick_delete(reverse("home_index"),
                 *[p.content_object for p in Proxy.objects.all()]
                 )

def setup_cache_signals():
    signals.post_save.connect(delete_proxy, sender=Proxy)

    signals.post_delete.connect(delete_content, sender=Post)
    signals.post_delete.connect(delete_content, sender=Quote)
    signals.post_delete.connect(delete_content, sender=Bookmark)

    signals.post_save.connect(delete_all, sender=BlogRoll)
    signals.post_delete.connect(delete_all, sender=BlogRoll)

    signals.post_save.connect(delete_all, sender=Category)
    signals.post_delete.connect(delete_all, sender=Category)

    signals.post_save.connect(delete_all, sender=Settings)

    signals.post_save.connect(delete_all, sender=SocialNetworkProfile)
    signals.post_delete.connect(delete_all, sender=SocialNetworkProfile)

    signals.post_save.connect(delete_all, sender=FlatBlock)
    signals.post_delete.connect(delete_all, sender=FlatBlock)

