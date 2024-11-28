from django.http import JsonResponse, HttpResponse


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