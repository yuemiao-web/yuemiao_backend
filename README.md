**该项目仅供学习，如用于商业用途，后果自负**

该项目中的接口调用使用了状态模式，有兴趣的朋友可以值得一学。

# 抢苗程序
目前只支持知苗易约小程序

## 功能
+ 一键预约疫苗（约成功过一次海口的）
+ 定时预约疫苗（缺点sessionId会过期）
+ 定时预约失败后重试策略(未经测试)
+ 使用代理ip池

## 技术栈
+ Django3
+ python3.6.13

## 开发环境启动
1. 安装依赖`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
2. 数据库账号密码修改成自己的，在miao_backend/miao_backend/settings.py中DATABASES字段修改对应字段
3. python manage.py makemigrations
4. python manage.py migrate
5. 启动`python manage.py runserver`

## 使用说明

1. 分别将前后端服务启动起来。访问http://localhost:3000
2. 通过fiddler抓包知苗易约小程序的登录sessionId。
3. 把sessionId填入页面中，选择和填写相应信息就可以点击预约或定时预约了。

## 当前问题
1. 获取约苗时间失败，因为数据被AES加密了，加密的key是微信的用户接口返回结果签名前16位，关键在于获取到加密的key。办法参考如下：
+ [charles实现微信小程序抓包](https://www.52pojie.cn/forum.php?mod=viewthread&tid=1145984&highlight=%CE%A2%D0%C5%D0%A1%B3%CC%D0%F2)
+ [有关ssl-pinning的总结](https://www.jianshu.com/p/22b56d977825)
+ [利用Xposed+JustTrustMe绕过Android App（途牛apk）的SSL Pinning](https://blog.csdn.net/weixin_44677409/article/details/106663127)
+ [当你写爬虫抓不到APP请求包的时候该怎么办？【初级篇】](https://zhuanlan.zhihu.com/p/46433599)

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