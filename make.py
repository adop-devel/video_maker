__author__ = 'sunjung@adop.cc'

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir

import re
import os
import numpy
import cv2
import time
from PIL import ImageFont, ImageDraw, Image


def combine_images_with_anchor(image1, image2, anchor_y, anchor_x):
    foreground, background = image1.copy(), image2.copy()
    # Check if the foreground is inbound with the new coordinates and raise an error if out of bounds
    background_height = background.shape[1]
    background_width = background.shape[1]
    foreground_height = foreground.shape[0]
    foreground_width = foreground.shape[1]
    if foreground_height + anchor_y > background_height or foreground_width + anchor_x > background_width:
        raise ValueError("The foreground image exceeds the background boundaries at this location")

    # do composite at specified location
    start_y = anchor_y
    start_x = anchor_x
    end_y = anchor_y + foreground_height
    end_x = anchor_x + foreground_width
    background[start_y:end_y, start_x:end_x, :] = foreground
    return background


def setText(timg):
    img_pil = Image.fromarray(timg)
    draw = ImageDraw.Draw(img_pil)
    draw.text((80, videoHeight - 55), description[idx], font=font, fill=(255, 255, 255, 100))
    timg = numpy.array(img_pil)
    return timg


def transForm(timg):
    th, tw = timg.shape[:2]

    M = numpy.float32([[1, 0, 100], [0, 1, 50]])

    img2 = cv2.warpAffine(timg, M, (tw, th))
    return img2


def fadeIn(timg, frm):
    for IN in range(0, 15):
        fadein = IN / 30.0
        dst = cv2.addWeighted(timg, fadein, timg, fadein, 0)
        frm.append(dst)


def fadeOut(timg, frm):
    for OUT in range(15, 0, -1):
        fOut = OUT / 30.0
        dst = cv2.addWeighted(timg, fOut, timg, fOut, 0)
        frm.append(dst)

videoWidth = 640
videoHeight = 360

expandWidth = 880
expandHeight = 480

initWidth = 0
initHeight = 0

path = './images'
paths = [os.path.join(path, i) for i in os.listdir(path) if re.search(".jpg$", i)]

logoPath = './adop_logo.png'
introPath = './assets/adop-intro-1080.jpg'

introImg = cv2.imread(introPath)
introImg = cv2.resize(introImg, (videoWidth, videoHeight))

logoImg = cv2.imread(logoPath)
logoImg = cv2.resize(logoImg, (40, 40))
pathOut = './news.mp4'
fps = 15
frame_array = []
fontpath = "fonts/adop.ttf"
font = ImageFont.truetype(fontpath, 20)

description = ['밥블레스유2 김숙vs제시vs박나래, 즉석 팔씨름 대회의 승자는?', '두번째 소식은 무엇?', '세번째 소식은 또 무엇?']

fadeIn(introImg, frame_array)

for i in range(0, 15):
    frame_array.append(introImg)

for idx, path in enumerate(paths):
    img = cv2.imread(path)
    fixedWidth = 0
    fixedHeight = 0

    mainWPos = 0
    mainHPos = 0
    for i in range(1, expandHeight - videoHeight + 1):
        if idx % 2 == 0:
            initWidth = expandWidth - i * 2
            initHeight = expandHeight - i
        else:
            initWidth = videoWidth + i * 2
            initHeight = videoHeight + i

        if img.shape[1] / img.shape[0] > initWidth / initHeight:
            fixedWidth = initWidth
            fixedHeight = round(initWidth / img.shape[1] * img.shape[0])
            mainWPos = 0
            mainHPos = round((initHeight - fixedHeight) / 2)
        else:
            fixedHeight = initHeight
            fixedWidth = round(initHeight / img.shape[0] * img.shape[1])
            mainWPos = round((initWidth - fixedWidth) / 2)
            mainHPos = 0

        mainImg = img.copy()

        mainImg = cv2.resize(mainImg, (fixedWidth, fixedHeight))

        overlay = img.copy()
        overlay = cv2.resize(overlay, (initWidth, initHeight))
        bg = cv2.blur(overlay, (30, 30))
        videoImg = combine_images_with_anchor(mainImg, bg, mainHPos, mainWPos)

        x, y, w, h = 0, videoHeight - 70, videoWidth, 50
        sub_img = videoImg[y:y + h, x:x + w]
        white_rect = numpy.ones(sub_img.shape, dtype=numpy.uint8) * 0
        res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

        # Putting the image back to its position
        videoImg[y:y + h, x:x + w] = res
        videoImg = combine_images_with_anchor(logoImg, videoImg, videoHeight - 65, 5)

        croppedImg = videoImg[0:videoHeight, 0:videoWidth]
        croppedImg = setText(croppedImg)

        height, width, layers = croppedImg.shape
        size = (width, height)

        if idx == 0 and i == 1:
            fadeOut(introImg, frame_array)
            fadeIn(croppedImg, frame_array)
        elif idx != 0 and i == 1:
            fadeIn(croppedImg, frame_array)

        frame_array.append(croppedImg)

        if i == expandHeight - videoHeight:
            fadeOut(croppedImg, frame_array)

    # frame_array.append()

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(pathOut, fourcc, fps, size)

for i in range(len(frame_array)):
    # writing to a image array
    out.write(frame_array[i])

out.release()

os.system("ffmpeg -i news.mp4 -vcodec libx264 news2.mp4")