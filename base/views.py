import os
import json
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

BASE_DIR = "./root"

def build_tree(path, rel_path=""):
    """Recursively build a tree of HTML files only."""
    tree = []
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        return tree

    for item in items:
        abs_item_path = os.path.join(path, item)
        rel_item_path = os.path.join(rel_path, item)

        if os.path.isdir(abs_item_path):
            tree.append({
                "name": item,
                "type": "dir",
                "children": build_tree(abs_item_path, rel_item_path),
            })
        else:
            if not item.endswith('.html'):
                continue
            tree.append({
                "name": item[:-5],  # remove '.html' from name
                "type": "file",
                "path": rel_item_path.replace("\\", "/"),  # for Windows
            })
    return tree

@login_required(login_url="login")
def list_files(request):
    abs_path = os.path.abspath(BASE_DIR)
    if not os.path.exists(abs_path):
        raise Http404("Root directory does not exist")

    file_tree = build_tree(abs_path)
    return render(request, "home.html", {"tree_json": json.dumps(file_tree)})

@login_required
def view_file(request, path):
    abs_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(abs_path):
        raise Http404("File not found")
    if not abs_path.endswith('.html'):
        return HttpResponse("Preview not available for non-HTML files.", status=400)

    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HttpResponse(content)

@login_required
def welcome(request):
    if request.method == "GET":
        return render(request, "welcome.html")