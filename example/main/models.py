from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Poem(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(Author)

    def __str__(self):
        return self.title


class Comment(models.Model):
    name = models.CharField(max_length=255)
    body = models.TextField()
    poem = models.ForeignKey(Poem)

    def __str__(self):
        return '%s @ %s' % (self.name, self.poem.title)
