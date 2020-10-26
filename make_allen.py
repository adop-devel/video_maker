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
import json
import time
from PIL import ImageFont, ImageDraw, Image

# 이미지가 확대 이동하는 동작?
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


def setText(timg, color, alignment):
    img_pil = Image.fromarray(timg)
    draw = ImageDraw.Draw(img_pil)
    draw.text((55, videoHeight - 325), description[idx], font=font, fill=color, align=alignment)
    ## 여기 수정하면 자막 높이조정 가능
    draw.text
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
def get_holes(image, thresh):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    im_bw = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)[1]
    im_bw_inv = cv2.bitwise_not(im_bw)

    contour, _ = cv2.findContours(im_bw_inv, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contour:
        cv2.drawContours(im_bw_inv, [cnt], 0, 255, -1)

    nt = cv2.bitwise_not(im_bw)
    im_bw_inv = cv2.bitwise_or(im_bw_inv, nt)
    return im_bw_inv


def remove_background(image, thresh, scale_factor=.25, kernel_range=range(1, 15), border=None):
    border = border or kernel_range[-1]

    holes = get_holes(image, thresh)
    small = cv2.resize(holes, None, fx=scale_factor, fy=scale_factor)
    bordered = cv2.copyMakeBorder(small, border, border, border, border, cv2.BORDER_CONSTANT)

    for i in kernel_range:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*i+1, 2*i+1))
        bordered = cv2.morphologyEx(bordered, cv2.MORPH_CLOSE, kernel)

    unbordered = bordered[border: -border, border: -border]
    mask = cv2.resize(unbordered, (image.shape[1], image.shape[0]))
    fg = cv2.bitwise_and(image, image, mask=mask)
    return fg

def logoOverlay(image,logo,alpha=1.0,x=0, y=0, scale=1.0):
    rows, cols, channels = logo.shape

    start_y = y;
    end_y = y+rows;

    start_x = x;
    end_x = x+cols;
## ㅁㄴㅇㄹㅁ
    roi = image[start_y:end_y, start_x:end_x, :]
    img2gray = cv2.cvtColor(logo,cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img2gray, 150, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)
    # Now black-out the area of logo in ROI
    img1_bg = cv2.bitwise_and(roi,roi,mask = mask_inv)
    # Take only region of logo from logo image.
    img2_fg = cv2.bitwise_and(logo,logo,mask = mask)
    # Put logo in ROI and modify the main image
    dst = cv2.add(img1_bg,img2_fg)

    image[start_y:end_y, start_x:end_x, :] = dst

    return image



videoWidth = 640
videoHeight = 360

expandWidth = 880
expandHeight = 480

initWidth = 0
initHeight = 0

# VIDEO_MAKER_PATH = '/Users/imac/project/video_maker/'
# VIDEO_MAKER_PATH = '/Data/video_maker/'
VIDEO_MAKER_PATH = '/Users/admin/git/video_maker/' # allen

path = '%simages' % VIDEO_MAKER_PATH
paths = [os.path.join(path, i) for i in os.listdir(path) if re.search(".(jpg|png|gif)$", i)]

logoPath = '%slogo' % VIDEO_MAKER_PATH
logoPath = [os.path.join(logoPath, i) for i in os.listdir(logoPath) if re.search(".(jpg|png|gif)$", i)]
paths.sort()

introPath = '%sassets/adop-intro-1080.jpg' % VIDEO_MAKER_PATH

introImg = cv2.imread(introPath)
# introImg = cv2.resize(introImg, (videoWidth, videoHeight)) // 이 부분을 주석하면 마지막에 adop 로고가 사라진다.

# logoImg = cv2.imread(logoPath[0],cv2.IMREAD_UNCHANGED)
# trans_mask = logoImg[:,:,2] == 0
# logoImg[trans_mask] = [255, 255, 255]
# logoImg = cv2.cvtColor(logoImg, cv2.COLOR_BGRA2BGR)

img = cv2.imread('/Users/admin/git/video_maker/logo/finalLike.png')
# nb_img = remove_background(img, 230)

logoImg = cv2.resize(img, (40, 40)) #이 부분을 주석하면 로고가 들어가지 않는다.

cv2.imshow('test',logoImg)
cv2.waitKey(1000)

clickImg = cv2.imread('/Users/admin/git/video_maker/logo/clickhere_final.png')
# nb_img = remove_background(img, 230)

clickImg = cv2.resize(clickImg, (126, 35)) #이 부분을 주석하면 로고가 들어가지 않는다.

# exit(0)
# cv2.COLOR_BGRA2RGB
infoJsonPath = '%sdescription/info.json' % VIDEO_MAKER_PATH
with open(infoJsonPath) as json_file:
    vInfoData = json.load(json_file)
print(vInfoData)
pathOut = '%svideo/news.mp4' % VIDEO_MAKER_PATH
fps = 15
frame_array = []

description = vInfoData['description']
## desc 가 너무 길시 줄이고 ... 처리
# for i in range(len(description)) :
#     if len(description[i]) >= 35 :
#         description[i] = description[i][0:35] + '....'

fontType = vInfoData['font']

fontpath = "%sfonts/%s" % (VIDEO_MAKER_PATH, fontType)
font = ImageFont.truetype(fontpath, int(vInfoData['font_size']))

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

        x, y, w, h = 0, videoHeight - 340, videoWidth, 50
        ## 여기의 videoHeight 를 바꾸면 회색 배경이 바뀐다.
        sub_img = videoImg[y:y + h, x:x + w]
        white_rect = numpy.ones(sub_img.shape, dtype=numpy.uint8) * 0
        res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)
        # cv2.imshow('test',logoImg)
        # cv2.waitKey(1000)

        # Putting the image back to its position
        videoImg[y:y + h, x:x + w] = res
        ## 여기를 수정하면 죄측 로고의 y 값이 변경된다.
        # logoOverLay  param 순서 ( 배경 이미지 , png 이미지, 1.0고정, x 위치, y 위치 )
        videoImg = logoOverlay( videoImg,logoImg, 1.0, 7 , 25)
        # combine_images_with_anchor 를 사용하면 기존의 이미지에 선택한 이미지를 원하는 우치에 넣을 수 있는것으로 보인다.
        ## allen - click 버튼을 이미지에 추가
        # videoImg = combine_images_with_anchor(videoImg,clickImg, videoHeight-180, videoWidth-110 ) # x, y
        videoImg = combine_images_with_anchor(clickImg,videoImg, videoHeight-120, videoWidth-140 ) # x, y



        croppedImg = videoImg[0:videoHeight, 0:videoWidth]
        croppedImg = setText(croppedImg, vInfoData['font_color'], vInfoData['alignment'])
        cv2.imshow('test',croppedImg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        break
        height, width, layers = croppedImg.shape
        size = (width, height)

        if idx == 0 and i == 1:
            # fadeOut(introImg, frame_array)
            fadeIn(croppedImg, frame_array)
        elif idx != 0 and i == 1:
            fadeIn(croppedImg, frame_array)

        frame_array.append(croppedImg)

        if i == expandHeight - videoHeight:
            fadeOut(croppedImg, frame_array)

fadeIn(introImg, frame_array)
fadeOut(introImg, frame_array)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(pathOut, fourcc, fps, size)

for i in range(len(frame_array)):
    # writing to a image array
    out.write(frame_array[i])

out.release()

finalMakeTask = "ffmpeg -i %svideo/news.mp4 -vcodec libx264 %svideo/final.mp4" % (VIDEO_MAKER_PATH, VIDEO_MAKER_PATH)
os.system(finalMakeTask)
finalVideoTask = "chmod 777 %svideo/final.mp4" % VIDEO_MAKER_PATH
os.system(finalVideoTask)
