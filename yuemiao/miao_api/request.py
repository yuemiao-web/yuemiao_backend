from yuemiao.miao_api.constants import USER_AGENT_COUNT, userAgents
from miao_backend.exceptions import BusinessException
import requests
import logging
from .util import getLatestDate, getZftsl
from requests.exceptions import Timeout
from json.decoder import JSONDecodeError
import time
from yuemiao.common.constant import baseUrl
import random
import json

log = logging.getLogger('log')
# 300: 该身份证或微信号已有预约信息 203: 校验信息错误
raiseErrCode = [300, 203]
retryNum = 5

proxyUseCount = 1
proxies = None

TIMEOUT = 10 # 10秒超时时间

def get_proxy_ip():
    global proxies
    if proxyUseCount < 10 and proxies:
        return proxies

    resOfProxy = requests.get('http://106.52.164.139:90/get/?type=https', timeout=TIMEOUT)
    proxy = json.loads(resOfProxy.content)
    p = proxy.get('proxy', None)
    if not p:
        raise(BusinessException('代理池没有代理ip了!'))
    proxies = {'https': f'https://{p}'}

    return proxies

def requestZMYY(url, sessionId, reqSeed=0, retryTime=0):
    global retryNum
    try:
        headers = {
            'Host': 'cloud.cn2030.com',
            'Connection': 'keep-alive',
            'Referer': 'https://servicewechat.com/wx2c7f0f3c30d99445/73/page-frame.html',
            'Cookie': sessionId,
            'content-type': 'application/json',
            'Accept-Encoding': 'gzip,compress,br,deflate'
        }
        headers['User-Agent'] = userAgents[random.randrange(0, USER_AGENT_COUNT)]
        headers['zftsl'] = getZftsl(0)
        log.info(f'请求url: {url}')
        res = requests.get(url, headers=headers, allow_redirects=False, timeout=TIMEOUT, proxies=proxies)
        if res.status_code == 302:
            res = requests.get(baseUrl + res.headers['Location'], headers=headers, timeout=TIMEOUT, proxies=proxies)
        
        reqSeed = getLatestDate(res.headers.get('Date'))
        if res.status_code == 500:
            # todo 重试机制需要优化，目前的处理方式可能导致一直重试
            # http 500状态码，可能是因为请求人数过多导致，重试
            log.error(f'http 500错误重试第{retryTime + 1}次!')
            if retryTime < retryNum:
                time.sleep(random.uniform(0.5, 1))
                return requestZMYY(url, sessionId, reqSeed, retryTime + 1)
            else:
                raise BusinessException(code=0, msg=f'http 500错误重试了{retryTime}次! 请稍后再试！')
        if res.status_code == 403:
            raise BusinessException(code=0, msg='接口报403, 被禁了或者是身份信息填写有误!')
        if res.status_code != 200:
            log.error(f'请求{url}错误，状态码{res.status_code}')
            raise BusinessException(code=0, msg=f'请求错误，状态码{res.status_code}')
        
        data = res.json()
        return data, reqSeed

    except Timeout as e:
        log.info(f'超时重试第${retryTime + 1}次!')
        if retryTime >= retryNum:
            time.sleep(random.uniform(0.5, 1))
            return requestZMYY(url, sessionId, 0, retryTime + 1)
        else:
            log.error(f'超时重试超过{retryNum}次，请检查网络是否连接正常!')
            raise BusinessException(code=0, msg='接口超时，请稍后重试！')
    except JSONDecodeError as e:
        log.error(f'返回结果序列化成json错误: {res.content.decode("utf8")}')
        raise e