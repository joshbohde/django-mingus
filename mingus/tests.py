from django.test.client import Client
from django.test import TestCase
from django.conf import settings
from staticgenerator import quick_delete
from basic.blog.models import Post, BlogRoll, Category, Settings
from basic.elsewhere.models import SocialNetworkProfile
from quoteme.models import Quote
from flatblocks.models import FlatBlock

import os

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
        path = os.path.join(settings.WEB_ROOT, *pages)
        self.assertTrue(os.access(path, os.F_OK),
                         "Page %s is not in the cache." % path)
        
    def assertCachedPageDoesNotExist(self, *pages):
        path = os.path.join(settings.WEB_ROOT, *pages)
        self.assertFalse(os.access(path, os.F_OK),
                         "Page %s is in the cache." % path)
        
    def test_HomePageCache(self):
        quick_delete("/")
        self.assertCachedPageDoesNotExist("index.html")
        self.test_HomePage()
        self.assertCachedPageExists("index.html")

    def test_ClearHomePageCacheOnEditPost(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        p = Post.objects.all()[0]
        p.title += "test"
        p.save()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnDeletePost(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        p = Post.objects.all()[0]
        p.delete()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnEditQuote(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q = Quote.objects.all()[0]
        q.slug += "-test"
        q.save()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnDeleteQuote(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        p = Quote.objects.all()[0]
        p.delete()
        self.assertCachedPageDoesNotExist("index.html")


    def test_ClearHomePageCacheOnEditBlogRoll(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q = BlogRoll.objects.all()[0]
        q.name += "-test"
        q.save()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnDeleteBlogRoll(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        p = BlogRoll.objects.all()[0]
        p.delete()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnEditCategory(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q = Category.objects.all()[0]
        q.title += "-test"
        q.save()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnDeleteCategory(self):
        c = Category.objects.create(title="foo", slug="test")
        c.save()
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        c.delete()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnEditSettings(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q = Settings.objects.all()[0]
        q.copyright = "test"
        q.save()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnEditSocialNetwork(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q = SocialNetworkProfile.objects.all()[0]
        q.name += "-test"
        q.save()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnDeleteSocialNetwork(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q = SocialNetworkProfile.objects.all()[0]
        q.delete()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnEditFlatBlock(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q =FlatBlock.objects.all()[0]
        q.header = "-test"
        q.save()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnDeleteFlatBlock(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q =FlatBlock.objects.all()[0]
        q.delete()
        self.assertCachedPageDoesNotExist("index.html")

    def test_ClearHomePageCacheOnEditBookmark(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q =Bookmark.objects.all()[0]
        q.url += "+foo"
        q.save()
        self.assertCachedPageDoesNotExist("index.html")


    def test_ClearHomePageCacheOnDeleteBookmark(self):
        self.test_HomePage()
        self.assertCachedPageExists("index.html")
        q =Bookmark.objects.all()[0]
        q.delete()
        self.assertCachedPageDoesNotExist("index.html")
