from django.db import models

# Create your models here.

class Message(models.Model):
  nickname = models.CharField(max_length=20)
  email = models.EmailField()
  date = models.DateField(auto_now=True)
  content = models.TextField()