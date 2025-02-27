from django.contrib.sitemaps import Sitemap
from django.urls import reverse, NoReverseMatch
from django.utils.translation import activate, get_language


class ChatStaticViewSitemap(Sitemap):
    changefreq = "daily"
    languages = ["es", "en-us", "en"]

    def items(self):
        # Return a list of named URLs from the chat app
        return ["chat:home", "chat:live-chat", "chat:close-chat"]

    def location(self, item):
        # Generate URLs dynamically using Django's reverse function
        return reverse(item)

    def priority(self, item):
        if item == "chat:home":
            return 1.0
        elif item == "chat:live-chat":
            return 0.9
        elif item == "chat:close-chat":
            return 0.3

    def get_urls(self, page=1, site=None, protocol=None):
        """
        Override get_urls to include alternate links for hreflang.
        """
        urls = super().get_urls(site=site, protocol=protocol)
        default_lang = get_language()  # Store the default language

        for url_info in urls:
            try:
                url_info["alternates"] = []
                for lang in self.languages:
                    activate(lang)  # Temporarily switch to the target language
                    alternate_url = reverse(url_info["item"])
                    url_info["alternates"].append(
                        {"hreflang": lang, "href": alternate_url}
                    )
            except NoReverseMatch:
                pass  # Skip if the URL doesn't exist in a specific language

        activate(default_lang)  # Restore the original language
        return urls
