import re

from django.conf import settings


import re
from django.conf import settings

def hreflang_context(request):
    """
    Context processor to add hreflang URLs for all supported languages.
    """
    path = request.path

    # Regex to match existing language prefixes in the URL (e.g., "/en/", "/fr/")
    lang_regex = r"^/({})/".format("|".join([re.escape(lang[0]) for lang in settings.LANGUAGES]))
    clean_path = re.sub(lang_regex, "/", path, count=1)  # Remove existing language prefix (if present)

    hreflang_urls = []
    for lang_code, _ in settings.LANGUAGES:
        lang_path = f"/{lang_code.rstrip('/')}{clean_path}"  # Add language prefix
        hreflang_urls.append({
            "lang": lang_code,
            "url": request.build_absolute_uri(lang_path),  # Build absolute URL
        })

    # Add the x-default fallback (without a language prefix)
    hreflang_urls.append({
        "lang": "x-default",
        "url": request.build_absolute_uri(clean_path if clean_path != "/" else "/"),
    })

    return {"hreflang_urls": hreflang_urls}
