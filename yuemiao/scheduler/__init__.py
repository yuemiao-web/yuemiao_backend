from miao_backend.exceptions import BusinessException
from apscheduler.events import EVENT_JOB_REMOVED
from yuemiao.sub_vac.sub_vac import SubscribeVaccine, requestOrderList
from yuemiao.models import SubInfoModel
from pytz import timezone
from django.forms.models import model_to_dict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings
from django_apscheduler.models import DjangoJobExecution
import logging
from datetime import datetime as dt, timedelta
import random

log = logging.getLogger('log')

# def delete_old_job_executions(max_age=604_800):
#     """This job deletes all apscheduler job executions older than `max_age` from the database."""
#     DjangoJobExecution.objects.delete_old_job_executions(max_age)

class Scheduler(BackgroundScheduler):
    def __init__(self) -> None:
        tz = timezone(settings.TIME_ZONE)
        jobstores = {
            'default': DjangoJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        job_defaults = {
            'coalesce': True,
            'max_instances': 3
        }

        super().__init__(jobstores=jobstores, executors=executors,
                         job_defaults=job_defaults, timezone=tz)
        
        self._init_event()
        
    def _init_event(self):
        def evtHandler(evt):
            if not evt.job_id:
                return
            
            log.info(f'job: {evt.job_id}被移除!')
            try:
                # 定时任务预约失败，将数据标为清除。就不会再跑定时了。
                subInfo = SubInfoModel.objects.get(id=evt.job_id)
                subInfo.deleted = True
                subInfo.save()
            except:
                pass

        self.add_listener(evtHandler, EVENT_JOB_REMOVED)

scheduler = Scheduler()
scheduler.start()

def subVac(subInfoId=None):
    log.info(f'定时任务执行, 预定信息id: {subInfoId}')
    subInfo = SubInfoModel.objects.get(id=subInfoId)
    info = model_to_dict(subInfo)
    
    def handleFail():
        # 预约失败处理，隔30秒刷新一次，5小时后没预约成功就暂停
        if not subInfo.retryStartTime:
            now = dt.now()
            offset = timedelta(hours=3)
            endtime = (now + offset).strftime('%Y-%m-%d %H:%M:%S')

            subInfo.retryStartTime = now
            subInfo.save()
        else:
            startTime = subInfo.retryStartTime
            offset = timedelta(hours=3)
            endtime = (startTime + offset).strftime('%Y-%m-%d %H:%M:%S')
        
        second = random.randint(20, 60)
        scheduler.reschedule_job(subInfoId, trigger=CronTrigger(second='*/' + str(second), end_date=endtime), jobstore='default')

    try:
        subVac = SubscribeVaccine(info)
        success = subVac.runStep()
        if success:
            # 预约成功处理
            subInfo.subSuccess = True
            subInfo.save()
            # todo 发送预约成功邮件
        else:
            handleFail()
    except Exception as e:
        handleFail()

# @scheduler.scheduled_job('cron', id='hold_session', name='hold_session', minute='*/40')
def holdSession():
    '''
    保持session会话定时任务，否则session会过期
    '''
    log.info('开始执行保持session会话定时任务...')
    subInfos = SubInfoModel.objects.filter(havePay=False, deleted=False)
    for info in subInfos:
        try:
            requestOrderList(info.sessionId)
        except BusinessException as e:
            # todo 这里保持会话失败了，考虑把deleted字段置为true，或者发送邮件通知用户更新sessionId
            log.error(f'{info.cname}的session会话保持失败! sessionId: {info.sessionId}')
            log.error(e)
    
    # 修改时间，使更加随机，避免被禁
    minute = random.randint(35, 55)
    srcond = random.randint(0, 60)
    scheduler.reschedule_job('hold_session', trigger=CronTrigger(minute='*/' + str(minute), second=srcond), jobstore='default')

