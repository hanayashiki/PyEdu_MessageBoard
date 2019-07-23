from main.models import Message

for i in range(100):
  Message.objects.create(nickname="unk", email="494450105@qq.com", content="abcde fgh ij.\nklmn opq.")