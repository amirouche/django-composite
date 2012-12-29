from django.contrib import admin

from models import Author
from models import Comment
from models import Poem


admin.site.register(Author)
admin.site.register(Comment)
admin.site.register(Poem)
