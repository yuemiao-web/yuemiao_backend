# 后端
## 技术栈
+ Django3
+ python3

## 开发环境启动
1. 安装依赖`pip install -r requirements.txt`
2. 数据库账号密码修改成自己的，在miao_backend/miao_backend/settings.py中DATABASES字段修改对应字段
3. python manage.py makemigrations
4. python manage.py migrate
5. 启动`python manage.py runserver`

## 问题记录

1. 关于返回408状态码，与请求太快有关，想一个策略尽量缩短请求间间隔。
2. 以下错误的原因有两种猜测：1 和网速慢有关；
```
raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='sc', port=443): Max retries exceeded with url: /wx/HandlerSubscribe.ashx?act=GetCustSubscribeDateAll
```

ASP.NET_SessionId=0bmjrte3lmvj3sjrsvcjri52
3. http状态码503和其他情况的处理方式，需要加入几个新的状态机来处理这种情况的重试。
4. 有被封禁的可能，封号之后请求一直是报403 http码，目前想到的原因可能是因为请求太快了。无法确定后台是根据什么封禁sessionId的。即使换了sessionId后也还是报403。一定时间后会回复。
5. 有被封号的可能，封号之后请求一直是报403 http码，目前想到的原因可能是因为请求太快了。
6. sessionId和用户代理是绑定的