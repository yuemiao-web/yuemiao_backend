from json.decoder import JSONDecodeError
from yuemiao.captcha.rotate import rotateCaptcha
from requests.exceptions import Timeout
from yuemiao.miao_api.util import getLatestDate
from django.http.response import HttpResponse
from miao_backend.exceptions import BusinessException
from yuemiao.captcha.slide import SlideCaptcha
from yuemiao.sub_vac.util import dict2query, getCurYearMon, save_base64_to_img
from yuemiao.miao_api.request import requestZMYY, retryNum
from yuemiao.common.constant import commonUrl
import logging
import random
import time

log = logging.getLogger('log')

class SubscribeVaccine():
    # 300: 该身份证或微信号已有预约信息 203: 校验信息错误
    raiseErrCode = [300, 203]

    def __init__(self, subInfo) -> None:
        self.currStep = QueryAvaliableDateStep(self)
        self.subInfo = subInfo
        self.reqSeed = 0

        self.vacId = subInfo['vacId']
        self.vacName = subInfo['vacName']
        self.hosId = subInfo['hosId']
        self.sessionId = subInfo['sessionId']
    
    def setSubInfo(self, key, value):
        self.subInfo[key] = value

    def getSubInfo(self, key):
        return self.subInfo[key]

    def setStep(self, step):
        self.currStep = step

    def runStep(self):
        return self.currStep.run()
    
    def request(self, url, successCode=200):
        log.info(f'zstl加密种子: {self.reqSeed}')
        data, reqSeed = requestZMYY(url, self.sessionId, 0, successCode)
        self.reqSeed = reqSeed

        if 'GetCaptcha' not in url and 'UserSubcribeList' not in url:
            log.info(f'接口返回结果: {data}')
        if data['status'] == 408:
            raise BusinessException(code=0, msg='接口出现408错误，请检查sessionId是否过期和程序请求逻辑是否有问题!')
        if data['status'] in self.raiseErrCode:
            raise BusinessException(code=0, msg=data['msg'])
        if data['status'] != successCode:
            log.error(f'知苗易约接口{url}请求错误, data: {data}, 指定成功码为: {successCode}')
            return None
        
        return data

class BaseStep():
    def __init__(self, context: SubscribeVaccine, prevStep = None) -> None:
        self.context = context
        self.prevStep: BaseStep = prevStep

    def run(self):
        pass

    def rollbackPrevStep(self):
        if not self.prevStep:
            return
        self.context.setStep(self.prevStep)
        return self.context.runStep()

class QueryAvaliableDateStep(BaseStep):
    def __init__(self, context: SubscribeVaccine, prevStep=None) -> None:
        super().__init__(context, prevStep=prevStep)

    def run(self):
        vacId = self.context.vacId
        vacName = self.context.vacName
        hosId = self.context.hosId

        log.info(f'获取疫苗<<{vacId}-{vacName}>>可预定的日期')
        month = getCurYearMon()
        url = f'{commonUrl}?act=GetCustSubscribeDateAll&pid={vacId}&id={hosId}&month={month}'
        res = self.context.request(url)
        
        dateList = res['list']
        dateAvaliableList = []
        for dateItem in dateList:
            if dateItem['enable']:
                log.info(f'{dateItem["date"]}可预约')
                dateAvaliableList.append(dateItem['date'])
        
        # 打乱顺序
        random.shuffle(dateAvaliableList)
        self.context.setStep(QueryAvaliableTimeStep(self.context, self, dateAvaliableList))
        time.sleep(0.5)
        return self.context.runStep()    

class QueryAvaliableTimeStep(BaseStep):
    def __init__(self, context: SubscribeVaccine, prevStep, dateAvaliableList: list) -> None:
        super().__init__(context, prevStep=prevStep)

        self.iter = iter(dateAvaliableList)

    def run(self):
        vacId = self.context.vacId
        hosId = self.context.hosId
        try:
            date = next(self.iter)
            self.context.setSubInfo('date', date)

            log.info(f'获取{date}可预定的时间')
            url = f'{commonUrl}?act=GetCustSubscribeDateDetail&pid={vacId}&id={hosId}&scdate={date}'
            res = self.context.request(url)

            timeList = res['list']
            mxidList = []
            for timeItem in timeList:
                if timeItem['qty'] > 0:
                    log.info(f'获取到mxid: {timeItem["mxid"]}')
                    mxidList.append(timeItem['mxid'])
            
            # 打乱顺序
            random.shuffle(mxidList)
            self.context.setStep(SubmitOrderStep(self.context, self, mxidList))
            time.sleep(0.5)
            return self.context.runStep()
        except StopIteration:
            name = self.context.getSubInfo('cname')
            raise BusinessException(code=0, msg=f'{name}预定疫苗失败!!!!!!!!!!!')

class SubmitOrderStep(BaseStep):
    def __init__(self, context: SubscribeVaccine, prevStep, mxidList) -> None:
        super().__init__(context, prevStep=prevStep)

        self.iter = iter(mxidList)

    def run(self):
        loop = True
        subSuccess = False
        while loop:
            try:
                mxid = next(self.iter)
                for i in range(5):
                    guid = self.captchaVerify()
                    if guid:
                        break
            
                if not guid:
                    raise BusinessException('滑块验证码校验失败，请检查程序是否正常!')
                
                time.sleep(random.uniform(0.1, 0.7))
                for i in range(5):
                    res = self.saveOrder(mxid, guid)
                    if res:
                        break

                    time.sleep(random.uniform(0.4, 0.7))
                if not res:
                    raise BusinessException('订单提交失败!')

                time.sleep(random.uniform(0.4, 0.7))
                success = self.queryOrderStatus()
                if success:
                    cname = self.context.getSubInfo('cname')
                    log.info(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    log.info(f'!!!!!!!!!!!!!{cname}预定成功!!!!!!!!!!!!!!!')
                    log.info(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    subSuccess = True
                    loop = False
            except StopIteration:
                log.info(f'提交失败，尝试其他日期')
                loop = False
                return self.rollbackPrevStep()

        return subSuccess

    def captchaVerify(self):
        '''
        识别滑块验证码
        '''
        log.info('获取滑块验证码')
        for i in range(5):
            res = self.context.request(f'{commonUrl}?act=GetCaptcha', 0)
            dragon = f'{res["dragon"]}'
            tiger = res.get('tiger', None)
            save_base64_to_img(dragon, './dragon.png')
            if tiger:
                save_base64_to_img(tiger, './tiger.png')
            
            if res['msg'] == 'ROTATE': # 判断是否是旋转验证码
                rotated_image = rotateCaptcha.rotateCaptcha.getImgFromDisk('./dragon.png')
                predicted_angle = rotateCaptcha.predictAngle(rotated_image)  # 预测还原角度
                x = 360 - predicted_angle
                time.sleep(random.uniform(0.5, 1))
            else:
                verify = SlideCaptcha(tiger, dragon, './res.png')
                x = verify.discern()
                time.sleep(random.uniform(0.5, 1))
            log.info(f'滑块验证码识别结果: {x}')
            
            token = res.get('payload', {}).get('SecretKey', None)
            verRes = self.context.request(f'{commonUrl}?act=CaptchaVerify&token={token}&x={x}&y=5')
            if verRes['status'] == 201:
                if i == 5:
                    raise BusinessException(code=0, msg=f'出现201错误重试5次! 请稍后再试！')
                else:
                    continue
            if not verRes:
                log.info(f'滑块验证码验证失败!')
                return None
            if verRes['status'] == 200:
                return verRes['guid']
            log.info(f'出现201错误码，重试第{i + 1}次!')

    def saveOrder(self, mxid, guid):
        '''
        下单
        '''
        userInfo = {
            'birthday': self.context.getSubInfo('birthday'),
            'tel': self.context.getSubInfo('tel'),
            'sex': self.context.getSubInfo('sex'),
            'cname': self.context.getSubInfo('cname'),
            'doctype': self.context.getSubInfo('doctype'),
            'idcard': self.context.getSubInfo('idcard'),
            'mxid': mxid,
            'date': self.context.getSubInfo('date'),
            'pid': self.context.vacId,
            'Ftime': self.context.getSubInfo('ftime'),
            'guid': guid
        }
        log.info(f'开始下单, 下单参数: {userInfo}')
        orderParams = dict2query(userInfo)
        res = self.context.request(f'{commonUrl}?act=Save20&{orderParams}')
        if not res:
            log.info(f'订单提交失败!')
            return False

        log.info(f'订单提交成功!')
        return True
    
    def queryOrderStatus(self):
        url = f'{commonUrl}?act=GetOrderStatus'
        res = self.context.request(url)
        
        return bool(res)

def requestOrderList(sessionId = None):
    '''
    查询历史订单数据
    '''
    url = f'{commonUrl}?act=UserSubcribeList'
    res, reqSeed = requestZMYY(url, sessionId, 0)
    
    log.info(f'历史订单查询结果{res}')
    if res['status'] != 200:
        return BusinessException(code=0, msg='查询失败!')
