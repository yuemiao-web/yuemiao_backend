from datetime import datetime
import cv2
import base64
import numpy as np

def getCurYearMon():
    now = datetime.now()
    return str(now.year) + str(now.month)

def dict2query(map):
    queryParams = ''
    for key, value in map.items():
        queryParams = queryParams + f'&{key}={value}'
    
    return queryParams[1:]

def save_base64_to_img(base64Str, imgName):
    imgdata=base64.b64decode(base64Str)
    file=open(imgName,'wb')
    file.write(imgdata)
    file.close()

def base64_to_image(base64_code, imgType=cv2.IMREAD_COLOR):
    # base64解码
    img_data = base64.b64decode(base64_code)
    # 转换为np数组
    img_array = np.fromstring(img_data, np.uint8)
    # 转换成opencv可用格式
    img = cv2.imdecode(img_array, imgType)
 
    return img