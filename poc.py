import hashlib
import hmac
import requests
import random

def getSecret():
    m = hashlib.md5()
    m.update('Add promo code')
    return m.hexdigest().encode('base64').strip()


SECRET = 'MzgyM2YwNDdiNTkwNjhlY2JmNWNjNjQ5ODdiYjI0ZjU=' # get_secret()
API_BASE_URL = 'https://api4.neuralprisma.com'

UPLOAD_IMAGE_URL = '/upload/image'
PROCESS_IMAGE_URL = '/process_direct/%s/%s?mode=freeaspect'
DEVICE_ID = ''.join([random.choice('0123456789abcdef') for _ in range(16)])


def getSignature(imageArray):
    message = imageArray[0:42]+imageArray[-42:]
    return hmac.new(SECRET, message, digestmod=hashlib.sha256).digest().encode('base64').strip()

def uploadImage(filename):
    global API_BASE_URL
    imageArray = open(filename,'rb').read()
    headers = {'User-Agent': 'Prisma (178; Samsung Galaxy - 6.0.0 - API 23 - 768x1280; Android 6.0; pie unknown)',
                'Content-Type': 'image/jpeg',
                'prisma-device-id': DEVICE_ID,
                'prisma-image-sign' : getSignature(imageArray)
    }
    r = requests.post(API_BASE_URL + UPLOAD_IMAGE_URL, headers=headers, data=imageArray)
    jsonResult = r.json()
    '''
    {u'status': u'ok', u'upload_status': u'received', u'id': u'310bf78b-8c74-49e7-8f47-d59be8818eef_us', u'api_base_url': u'https://api4.neuralprisma.com'}
    '''
    if jsonResult['status'] == 'ok' and jsonResult['upload_status'] == 'received':
        API_BASE_URL = jsonResult['api_base_url']
        return jsonResult['id']
    else:
        return None

def processImage(uid, style, filename):
    headers = {'User-Agent': 'Prisma (178; Samsung Galaxy - 6.0.0 - API 23 - 768x1280; Android 6.0; pie unknown)',
                'prisma-device-id': DEVICE_ID
    }
    r = requests.get(API_BASE_URL + (PROCESS_IMAGE_URL % (uid, style)), headers=headers, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)

def main():
    uid = uploadImage('image.jpg')
    if uid is not None:
        processImage(uid, 's_line', 'image_s_line.jpg')
        processImage(uid, 'q5', 'image_q5.jpg')

if __name__ =='__main__':
	main()