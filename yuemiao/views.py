from miao_backend.exceptions import BusinessException
from urllib import parse
from apscheduler.triggers.cron import CronTrigger

from pytz import timezone
from yuemiao.models import SubInfoModel
from yuemiao.sub_vac.sub_vac import SubscribeVaccine, requestOrderList
from .miao_api.request import requestZMYY
from yuemiao.scheduler import scheduler, subVac
import logging
from miao_backend.common.response import GenericResponse
from yuemiao.common.constant import commonUrl
from django.views.decorators.http import require_http_methods
from django.db.transaction import atomic
from datetime import datetime as dt
import json

log = logging.getLogger('log')
@require_http_methods(['GET'])
def queryHospital(request):
    params = request.GET
    city = parse.quote(params['city'])
    cityCode = params['cityCode']
    vacTypeId = params['vacTypeId']
    sessionId = params['sessionId']
    url = f'{commonUrl}?act=CustomerList&city={city}&id=0&cityCode={cityCode}&product={vacTypeId}'

    res, reqSeed = requestZMYY(url, sessionId, 0)
    log.info(f'查询医院返回结果: {res}')
    if res['status'] != 200:
        return GenericResponse(code=0, msg='查询失败!')

    hospitals = res['list']
    return GenericResponse(hospitals)

@require_http_methods(['GET'])
def queryVacOfHospital(request):
    params =request.GET
    hosId = params['hosId']
    sessionId = params['sessionId']
    url = f'{commonUrl}?act=CustomerProduct&id={hosId}'
    res, reqSeed = requestZMYY(url, sessionId, 0)
    if res['status'] != 200:
        return GenericResponse(code=0, msg='查询失败!')

    vaccineList = res['list']
    return GenericResponse(vaccineList)

@require_http_methods(['POST'])
def subscribe(request):
    params = json.loads(request.body)
    log.info(f'传入参数: {params}')
    sub = SubscribeVaccine(params)
    res = sub.runStep()
    if res:
        return GenericResponse(msg='恭喜，预约成功！')
    
    return GenericResponse(code=0, msg='很遗憾，没有预约成功!')

@require_http_methods(['POST'])
def timedSub(request):
    params = json.loads(request.body)
    subInfo = params.get('subInfo')
    cronInfo = params.get('cronInfo')
    try:
        sessionId = subInfo.get('sessionId')
        log.info(f'检查sessionId有效性: {sessionId}')
        requestOrderList(sessionId)
    except BusinessException as e:
        raise BusinessException(code=0, msg='添加定时任务失败! 该sessionId不可用!')

    ## 将数据保存至数据库
    subInfo = SubInfoModel(**subInfo)
    subInfo.save()

    ## 设置定时任务
    scheduler.add_job(subVac, 'cron', year='*', month=cronInfo['month'],
        day=cronInfo['day'], hour=cronInfo['hour'], minute=cronInfo['min'],
        second=cronInfo['sec'], args=(subInfo.id,), id=str(subInfo.id))

    return GenericResponse(msg='设置定时预约成功!')