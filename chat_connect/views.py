from xml.etree.ElementTree import Element, SubElement, tostring

from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"})


def robots_txt(request):
    content = """User-agent: Googlebot
Disallow:

User-agent: *
Disallow: /

Sitemap: https://chatea-conecta.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")


def multilingual_sitemap(request, sitemaps, **kwargs):
    """
    Custom sitemap view to include hreflang links.
    """

    current_site = get_current_site(request)

    # Parse the XML content
    root = Element(
        "urlset",
        {
            "xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "xmlns:xhtml": "http://www.w3.org/1999/xhtml",
        },
    )

    for section, site in sitemaps.items():
        for url_info in site.get_urls(site=current_site, protocol=request.scheme):
            url = SubElement(root, "url")
            loc = SubElement(url, "loc")
            loc.text = url_info["location"]

            if "alternates" in url_info:
                for alternate in url_info["alternates"]:
                    link = SubElement(
                        url,
                        "{http://www.w3.org/1999/xhtml}link",
                        {
                            "rel": "alternate",
                            "hreflang": alternate["hreflang"],
                            "href": alternate["href"],
                        },
                    )

            if "changefreq" in url_info:
                changefreq = SubElement(url, "changefreq")
                changefreq.text = url_info["changefreq"]

            if "priority" in url_info:
                priority = SubElement(url, "priority")
                priority.text = str(url_info["priority"])

    # Generate the XML string
    sitemap_xml = tostring(root, encoding="utf-8", method="xml")

    # Return the modified sitemap XML
    return HttpResponse(sitemap_xml, content_type="application/xml")
