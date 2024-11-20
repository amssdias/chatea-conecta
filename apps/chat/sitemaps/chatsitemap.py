from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class ChatStaticViewSitemap(Sitemap):
    changefreq = "daily"

    def items(self):
        # Return a list of named URLs from the chat app
        return ['chat:home', 'chat:live-chat', 'chat:close-chat']

    def location(self, item):
        # Generate URLs dynamically using Django's reverse function
        return reverse(item)

    def priority(self, item):
        if item == 'chat:home':
            return 1.0
        elif item == 'chat:live-chat':
            return 0.9
        elif item == 'chat:close-chat':
            return 0.3
