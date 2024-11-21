import re

from django.conf import settings


def hreflang_context(request):
    """
    Context processor to add hreflang URLs for all supported languages.
    """
    path = request.path

    # Regex to match existing language prefixes in the URL
    lang_regex = r"^/({})/".format("|".join([lang[0] for lang in settings.LANGUAGES]))
    clean_path = re.sub(lang_regex, "/", path)  # Remove existing language prefix

    hreflang_urls = []
    for lang_code, _ in settings.LANGUAGES:
        hreflang_urls.append({
            "lang": lang_code,
            "url": f"/{lang_code}{clean_path}",
        })

    # Add the x-default fallback (without a language prefix)
    hreflang_urls.append({
        "lang": "x-default",
        "url": clean_path,
    })

    return {"hreflang_urls": hreflang_urls}
