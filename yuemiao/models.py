from django.db import models

class SubInfoModel(models.Model):
    cname = models.CharField(max_length=50, verbose_name='姓名')
    sex = models.CharField(max_length=5, verbose_name='性别')
    tel = models.CharField(max_length=20, verbose_name='电话号码')
    birthday = models.CharField(max_length=20, verbose_name='生日')
    doctype = models.CharField(max_length=5, verbose_name='证件类型')
    idcard = models.CharField(max_length=30, verbose_name='证件号')
    sessionId = models.CharField(max_length=100, verbose_name='sessionId')
    hosId = models.CharField(max_length=10, verbose_name='预约的医院id')
    vacId = models.CharField(max_length=10, verbose_name='预约的疫苗id')
    vacName = models.CharField(max_length=50, verbose_name='预约的疫苗名称')
    ftime = models.CharField(max_length=5, verbose_name='预约针次')
    
    subSuccess = models.BooleanField(verbose_name='预约成功', default=False)
    havePay = models.BooleanField(verbose_name='预定成功后是否已付款', default=False)
    deleted = models.BooleanField(verbose_name='无用, 被删除的标志', default=False)
    retryStartTime = models.DateTimeField(null=True, verbose_name='重试开始时间')
    createTime = models.DateTimeField(auto_now_add=True)
    updateTime = models.DateTimeField(auto_now=True)
