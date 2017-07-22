import hashlib
import hmac
import requests
import random
import os
import urllib
import sys
import imghdr
import time
from Tkinter import Tk
from tkFileDialog import askopenfilename

def getSecret():
	m = hashlib.md5()
	m.update('Add promo code')
	return m.hexdigest().encode('base64').strip()


SECRET = 'MzgyM2YwNDdiNTkwNjhlY2JmNWNjNjQ5ODdiYjI0ZjU=' # get_secret()
API_BASE_URL = 'https://api4.neuralprisma.com'

UPLOAD_IMAGE_URL = '/upload/image'
GET_STYLE_URL = '/styles'
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

def getStyles():
	if not os.path.exists("styles"):
		os.makedirs("styles")
	if not os.path.exists("uploads"):
		os.makedirs("uploads")
	print("Loading Styles...")

	headers = {'User-Agent': 'Prisma (178; Samsung Galaxy - 6.0.0 - API 23 - 768x1280; Android 6.0; pie unknown)',
				'Content-Type': 'application/json; charset=UTF-8',
				'prisma-device-id': DEVICE_ID,
			}
	styles_data = '{"codes":["public","daily","segmentation_1704"],"ids":["8c7e701f-fdab-450d-bac0-bf46f4820490","17a684f8-212e-4fc8-9549-509e1345e96d","cdf4eff1-6b5c-4ee6-8daf-d06346f84394","b721e987-7022-4a57-b7c3-681ad5b3384e","7fcbd93a-962a-4ff4-9106-efbd40e1f05f","998d78c2-cc1e-497e-970a-cd7ae692e757","0040fbd5-c06f-46fe-b96d-1b5762c477e5","ab0062c2-96f8-4f2c-96cd-89291b54d6b7","b221ade3-54a3-4777-8b46-7f95269994a8","ad349d67-978b-43a0-afa7-d53995d868e7","5ac715fa-bca6-4949-a029-be81e2377351","783b5630-b3bb-4835-bdce-038652e80447","0b923dcd-4314-44c5-82de-577a9f1d4162","14dfaefe-f398-4e88-a2cb-3986fd06ff28","57b76c9d-2e0d-4ecc-9f79-d026d445a20e","602074d9-565b-4d57-bcf0-115da8e1de4f","a07857f3-fb0b-4451-9029-d49525337c89","399d24e9-29a6-4d5a-a1fc-7a214a248b99","73266911-b988-4c4a-a012-09f454980e23","b094639f-63ec-42b6-a479-61c92e6fd6ae","92ba485f-8ce9-4a63-837f-0908e015fe1a","07bd2862-82bd-4ffc-b283-2fff5a696ab2","f00b7e54-9efd-44fd-9e26-ed8983d70ebb","fff60a89-e63a-4cfa-9b3b-1016ce7624ce","1790fe08-e42c-48a8-ae13-b92ddf270a0e","62223f2e-b049-4651-a836-131279195b12","8ca0fadc-a3c8-4c09-bf3a-835ffaeaf958","5d250934-51aa-42e1-8bb8-215ca56d4222","032ff9f3-bf34-44b0-817c-0bbf37619cd0","c6fe5de4-f38c-4759-8f64-ab1e674db5f4","aeebb637-0c57-4d03-9133-7887266e0a48","3164f906-32ad-4cd4-b8cb-422d82e777c4","d9244a9a-e0b2-4f22-ba4b-a547a2cec819","ecb314f2-18c8-460d-9766-2eed770e1af6","c0522fc8-8fe6-4eb8-9318-b94860ee6fcf","28aa13e7-0f3a-440f-992c-0d66adcacff5","504f6fba-f276-4101-a6c4-3ff62553d645","38422a07-8b3d-4302-81f9-09743a900a13","8aa037f9-1d2f-4ff0-8a8d-65dae867433b","9126170c-c20f-4311-b767-732d0a2b63ed","683195d5-e5e9-48cd-b558-4fe1e6c04166"]}'
	r = requests.post(API_BASE_URL + GET_STYLE_URL, headers=headers, data=styles_data)
	if r.status_code != 200:
		print("Error in getting styles. Please try again later")
		exit()
	jsonResult = r.json()

	styles_arr = {}
	total_num_styles = len(jsonResult["styles"])
	for count,style in enumerate(jsonResult["styles"]):
		img_url = style["image_url"]
		model = style["model"]
		title = style["artwork"]
		styles_arr[title] = model
		if not os.path.isfile("styles/"+title+".jpg"):
			try:
				urllib.urlretrieve(img_url, "styles/"+title+".jpg")
			except:
				pass
		progressBar(count+1, total_num_styles)
	sys.stdout.write("\n")
	return styles_arr

def progressBar(value, endvalue, bar_length=20):
	percent = float(value) / endvalue
	arrow = '-' * int(round(percent * bar_length)-1) + '>'
	spaces = ' ' * (bar_length - len(arrow))
	sys.stdout.write("\rStyles loaded: [{0}] {1}%".format(arrow + spaces, int(round(percent * 100))))
	sys.stdout.flush()

def main():
	filename = chooseImage()
	styles_arr = getStyles()
	uid = uploadImage(filename)
	if uid is not None:
		while True:
			input_str = "Input style title from image names saved in styles folder(located in same directory as this script). 0 to exit : "
			style_title = raw_input(input_str).strip()
			if style_title=='0':
				exit()
			else:
				if style_title not in styles_arr:
					print("Invalid style image. Please try again")
					continue
				else:
					head, tail = os.path.split(filename)
					processImage(uid, styles_arr[style_title], "uploads/"+style_title+"_"+tail)
					print("Image saved as " + style_title+"_"+tail)

def chooseImage():
	Tk().withdraw()
	while True:
		filename = askopenfilename()
		if imghdr.what(filename) is None:
			print("Not a valid image file. Please try again")
			time.sleep(5)
		else:
			return filename
	

if __name__ =='__main__':
	main()