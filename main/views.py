from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponseForbidden
from django import forms

from main.models import Message

import time

# Create your views here.

MSG_PER_PAGE = 6                                                    # 每页多少个消息，为常量
MIN_CONTENT = 15
MAX_CONTENT = 2000
MIN_NEW_MESSAGE_INTERVAL = 5


class NewMessage(forms.Form):
  nickname = forms.CharField(max_length=Message._meta.get_field("nickname").max_length, min_length=1)
  email = forms.EmailField()
  content = forms.CharField(min_length=MIN_CONTENT, max_length=MAX_CONTENT, widget=forms.Textarea)


sessID_to_time = {}


def get_messages(lo: int, hi: int):
  messages = Message.objects.filter(id__gte=lo, id__lte=hi)         # 选取 Message 表中，id 大于等于 lo 小于等于 hi 的
  return [
    [m.id, m.nickname, m.email, m.date.isoformat(), m.content.split("\n")]
  for m in messages]


def new_message(request: HttpRequest):
  if request.method == 'POST':
    if not request.session.exists(request.session.session_key):
      return HttpResponseForbidden()
    else:
      sess_key = request.session.session_key
      if sess_key not in sessID_to_time:
        sessID_to_time[sess_key] = time.time()
      else:
        if time.time() - sessID_to_time[sess_key] < MIN_NEW_MESSAGE_INTERVAL:
          return index(request,
                       content_error=f"You should send message at least every {MIN_NEW_MESSAGE_INTERVAL} seconds.")
        sessID_to_time[sess_key] = time.time()

    request.session["cur_nickname"] = request.POST['nickname']
    request.session["cur_email"] = request.POST['email']
    request.session["cur_content"] = request.POST['content']
    f = NewMessage(request.POST)
    print("new_message: f.is_valid() =", f.is_valid())
    if not f.is_valid():
      return index(request,
                   form=f.as_table(),
                   nickname_error=str(f.errors['nickname'] if 'nickname' in f.errors else ""),
                   email_error=str(f.errors['email'] if 'email' in f.errors else ""),
                   content_error=str(f.errors['content'] if 'content' in f.errors else ""),
                   )
    else:
      Message.objects.create(
        nickname=f.cleaned_data['nickname'],
        email=f.cleaned_data['email'],
        content=f.cleaned_data['content'],
      )
      request.session["cur_content"] = ""
      return redirect("/index/")
  else:
    return index(request)


def index(request: HttpRequest, **kwargs):
  if "cur_nickname" not in request.session:
    request.session["cur_nickname"] = ""
    request.session["cur_email"] = ""
    request.session["cur_content"] = ""

  n_messages = Message.objects.count()
  n_pages = (n_messages + MSG_PER_PAGE - 1) // MSG_PER_PAGE         # 计算总页面数
  if "page" not in request.GET or not request.GET["page"].isnumeric:
    page_id = 0                                                     # 如果没有在 URL 中指定页面，或参数不是数字，返回第 0 页
  else:
    page_id = int(request.GET["page"])

  messages = get_messages(n_messages - MSG_PER_PAGE * (page_id + 1) + 1, n_messages - MSG_PER_PAGE * page_id)
                                                                    # 返回页面范围内的
  messages.sort(key=lambda x: x[0], reverse=True)                   # 按 id 进行倒序排列
  range_n_pages = zip(range(0, n_pages), range(1, n_pages + 1))     # 实际页和展示页的组合，一个是 0-indexed 一个是 1-indexed

  feed = dict(messages=messages,
              range_n_pages=range_n_pages,
              current_page=page_id,
              n_pages=n_pages,
              form=NewMessage().as_table(),
              nickname_error="",
              email_error="",
              content_error="",
              cur_nickname=request.session["cur_nickname"],
              cur_email=request.session["cur_email"],
              cur_content=request.session["cur_content"]
              )
  feed.update(kwargs)

  return render(request, 'index.html', feed)


def fake_index(request):
  comment1 = "I had the same issue where I keyboard on Pycharm was not responding anymore.\nThe following solved my issue both on Windows 10 and MacOsx\nClick on help on the menu"
  fake_messages = [
    [0, "Alice", "alice@g.com", time.asctime(time.gmtime(50000)), comment1.split("\n")],
    [1, "Bob", "bob@g.com", time.asctime(time.gmtime(56000)), comment1.split("\n")],
  ] * 4
  return render(request, 'index.html', { 'messages': fake_messages })

