from django.urls import path
from .views import list_files, view_file, welcome

urlpatterns = [
    path("view", list_files, name="list_files_root"),
    path("view/<path:path>/", view_file, name="view_file"),
    path("view/welcome", welcome, name="welcome")
]
