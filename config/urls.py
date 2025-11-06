from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "message": "Cupid API root",
        "profile": "/api/profile/"
    })

urlpatterns = [
    path('admin/', admin.site.urls),

    # include users app routes under /api/
    # users.urls defines "profile/" so full path becomes /api/profile/
    path('api/', include('users.urls')),

    # Redirect root "/" to /api/
    path('', RedirectView.as_view(url='/api/', permanent=False)),
]