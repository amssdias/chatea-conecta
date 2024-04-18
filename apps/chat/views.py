from django.shortcuts import render
from django.conf import settings

# Create your views here.
def test_request(request):
    print(settings.TEMPLATES)  # This will show your templates configuration
    for config in settings.TEMPLATES:
        print(config['DIRS'])
    return render(request, "chat.html")
