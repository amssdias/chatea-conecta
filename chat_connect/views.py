from urllib.parse import urlparse, urljoin
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"})


def robots_txt(request):
    content = """User-agent: *
Disallow:
Disallow: /chatea-admin/
Disallow: /ws/
Disallow: /close-chat/

Sitemap: https://chatea-conecta.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")


def build_production_url(url_or_path: str) -> str:
    """
    Build a production absolute URL from either a relative path or an absolute URL.
    """
    parsed_url = urlparse(url_or_path)

    if parsed_url.scheme and parsed_url.netloc:
        path = parsed_url.path
    else:
        path = url_or_path

    return urljoin(settings.SITE_URL.rstrip("/") + "/", path.lstrip("/"))


def multilingual_sitemap(request, sitemaps, **kwargs):
    """
    Custom sitemap view to include hreflang links.
    """

    current_site = get_current_site(request)
    site_url = settings.SITE_URL.rstrip("/")

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
            loc.text = build_production_url(url_info["location"])

            if "alternates" in url_info:
                for alternate in url_info["alternates"]:
                    link = SubElement(
                        url,
                        "{http://www.w3.org/1999/xhtml}link",
                        {
                            "rel": "alternate",
                            "hreflang": alternate["hreflang"],
                            "href": build_production_url(alternate["href"]),
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
