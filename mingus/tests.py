from django.test.client import Client
from django.test import TestCase
from django.conf import settings
from staticgenerator import quick_delete
from basic.blog.models import Post, BlogRoll, Category, Settings
from basic.bookmarks.models import Bookmark
from quoteme.models import Quote
from basic.elsewhere.models import SocialNetworkProfile
from flatblocks.models import FlatBlock


from functools import wraps
import os

def make_path(*pages):
    unabs = lambda p: p[1:] if os.path.isabs(p) else p
    pages = (unabs(p) for p in pages)
    path = os.path.join(settings.WEB_ROOT, *pages)
    return path

def clears_home(f):
    @wraps(f)
    def inner(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        f(self)
        self.assertCachedPageDoesNotExist("index.html")
    return inner

def clears_post(f):
    @wraps(f)
    def inner(self):
        p = self.test_PostCache()
        f(self)
        self.assertCachedPostDoesNotExist(p)
    return inner

class MingusClientTests(TestCase):
    
    fixtures = ['test_data.json', ]

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_HomePage(self):
        '''Test if the homepage renders.'''
        c = Client()
        response = c.get('/')
        self.failUnlessEqual(response.status_code, 200)

    def test_Homepage_Paging(self):
        '''
        Test paging the homepage list.

        '''

        #need to update blog Settings page size, it defaults to 20 but we
        #don't have 20 records to page. So we'll set it to 1 and we should be ok.
        from basic.blog.models import Settings
        settings = Settings.get_current()
        settings.page_size = 1
        settings.save()

        c = Client()
        response = c.get('/', {'page': 2},)
        self.failUnlessEqual(response.status_code, 200)

    def test_Search(self):
        '''Test search view.'''

        c = Client()
        response = c.get('/search/', {'q':'django'})

        #test success request
        self.failUnlessEqual(response.status_code, 200)

        #test result as expected
        self.assertEquals(response.context['object_list'][0].title, 'Django Community')

    def test_About(self):
        'Test if the about page renders.'
        c = Client()
        response = c.get('/about/')
        self.failUnlessEqual(response.status_code, 200)

    def test_Contact(self):
        'Test if the contact page renders.'
        c = Client()
        response = c.get('/contact/')

        self.failUnlessEqual(response.status_code, 200)

    def test_ContactSubmit(self):
        '''
        Test submitting the contact form. Expect to return to the form sent
        template.

        The field 'fonzie_kungfu' is the honeypot field to protect you from
        spam. This feature is provided by django-honeypot.

        '''
        c = Client()
        response = c.post('/contact/', {'name': 'charles',
                    'email': 'foo@foo.com', 'body': 'hello.',
                    'fonzie_kungfu': ''},
                    follow=True)
        self.failUnlessEqual(response.status_code, 200)

    def test_ContactSubmit_WithHoneyPot(self):
        '''Test the @honeypot decorator which exists to reduce spam.

        HoneyPot will return a 400 response if the honeypot field is
        submited with a value.

        '''
        c = Client()
        response = c.post('/contact/', {'name': 'charles', 'email':
                    'foo@foo.com', 'body': 'hello.', 'fonzie_kungfu': 'evil'},
                    follow=True)
        self.failUnlessEqual(response.status_code, 400)

    def test_Post(self):
        p = Post.objects.all()[0]
        c = Client()
        r = c.get(p.get_absolute_url())
        self.failUnlessEqual(r.status_code, 200)
        return p

    def test_QuoteList(self):
        '''Test quote list page renders.'''

        c = Client()
        response = c.get('/quotes/')
        self.failUnlessEqual(response.status_code, 200)

    def test_QuoteDetail(self):
        '''Test quote list page renders.'''

        from quoteme.models import Quote
        quote = Quote.objects.all()[0]

        c = Client()
        response = c.get(quote.get_absolute_url())
        self.failUnlessEqual(response.status_code, 200)


    def test_RSS(self):
        '''Test the latest posts feed displays.'''

        c = Client()
        response = c.get('/feeds/latest/')
        self.failUnlessEqual(response.status_code, 200)

    def test_SpringsteenFeed_Posts(self):
        '''
        Test the latest Post springsteen feed for findjango integration
        displays.
        '''

        c = Client()
        response = c.get('/api/springsteen/posts/')
        self.failUnlessEqual(response.status_code, 200)


    def test_SpringsteenFeed_Posts_ByCategory(self):
        '''
        Test the latest Post By Category springsteen feed for findjango
        integration displays.

        '''

        c = Client()
        response = c.get('/api/springsteen/category/django/')
        self.failUnlessEqual(response.status_code, 200)


    def assertCachedPageExists(self, *pages):
        path = make_path(*pages)
        self.assertTrue(os.access(path, os.F_OK),
                         "Page %s is not in the cache." % path)
        
    def assertCachedPageDoesNotExist(self, *pages):
        path = make_path(*pages)
        self.assertFalse(os.access(path, os.F_OK),
                         "Page %s is in the cache." % path)

    def assertCachedPostDoesNotExist(self, post):
        self.assertCachedPageDoesNotExist(post.get_absolute_url(), "index.html")
        
    def test_HomePageCache(self):
        quick_delete("/")
        self.assertCachedPageDoesNotExist("index.html")
        self.test_HomePage()
        self.assertCachedPageExists("index.html")

    def test_PostCache(self):
        p = self.test_Post()
        quick_delete(p.get_absolute_url())
        self.assertCachedPostDoesNotExist(p)
        p = self.test_Post()
        self.assertCachedPageExists(p.get_absolute_url(), "index.html")
        return p

    @clears_home
    @clears_post
    def test_ClearHomePageCacheOnEditPost(self):
        p = self.test_PostCache()
        p.title += "test"
        p.save()
        self.assertCachedPostDoesNotExist(p)

    @clears_home
    @clears_post
    def test_ClearHomePageCacheOnDeletePost(self):
        p = self.test_PostCache()
        p.delete()

    @clears_home
    def test_ClearHomePageCacheOnEditQuote(self):
        q = Quote.objects.all()[0]
        q.slug += "-test"
        q.save()

    @clears_home
    def test_ClearHomePageCacheOnDeleteQuote(self):
        q = Quote.objects.all()[0]
        q.delete()

    @clears_home
    @clears_post
    def test_ClearHomePageCacheOnEditBlogRoll(self):
        q = BlogRoll.objects.all()[0]
        q.name += "-test"
        q.save()

    @clears_home
    @clears_post
    def test_ClearHomePageCacheOnDeleteBlogRoll(self):
        b = BlogRoll.objects.all()[0]
        b.delete()

    @clears_home
    @clears_post
    def test_ClearHomePageCacheOnEditCategory(self):
        q = Category.objects.all()[0]
        q.title += "-test"
        q.save()

    @clears_home
    @clears_post    
    def test_ClearHomePageCacheOnDeleteCategory(self):
        c = Category.objects.create(title="foo", slug="test")
        c.save()
        clears_home(lambda self: c.delete())(self)

    @clears_home
    @clears_post    
    def test_ClearHomePageCacheOnEditSettings(self):
        q = Settings.objects.all()[0]
        q.copyright = "test"
        q.save()

    @clears_home
    @clears_post    
    def test_ClearHomePageCacheOnEditSocialNetwork(self):
        q = SocialNetworkProfile.objects.all()[0]
        q.name += "-test"
        q.save()

    @clears_home
    @clears_post    
    def test_ClearHomePageCacheOnDeleteSocialNetwork(self):
        q = SocialNetworkProfile.objects.all()[0]
        q.delete()

    @clears_home
    @clears_post    
    def test_ClearHomePageCacheOnEditFlatBlock(self):
        q =FlatBlock.objects.all()[0]
        q.header = "-test"
        q.save()

    @clears_home
    @clears_post    
    def test_ClearHomePageCacheOnDeleteFlatBlock(self):
        q =FlatBlock.objects.all()[0]
        q.delete()

    @clears_home
    def test_ClearHomePageCacheOnEditBookmark(self):
        q =Bookmark.objects.all()[0]
        q.url += "+foo"
        q.save()

    @clears_home
    def test_ClearHomePageCacheOnDeleteBookmark(self):
        q =Bookmark.objects.all()[0]
        q.delete()
