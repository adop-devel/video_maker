import re
import os
import numpy
import cv2
from PIL import ImageFont, ImageDraw, Image


def combine_two_color_images_with_anchor(image1, image2, anchor_y, anchor_x):
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

path = './images'
paths = [os.path.join(path, i) for i in os.listdir(path) if re.search(".jpg$", i)]

logoPath = './adop_logo.png'
logoImg = cv2.imread(logoPath)
logoImg = cv2.resize(logoImg,(40,40))
pathOut = './news.mp4'
fps = 0.2
frame_array = []
fontpath = "fonts/adop.ttf"
font = ImageFont.truetype(fontpath, 20)

videoWidth = 640
videoHeight = 360

description = ['밥블레스유2 김숙vs제시vs박나래, 즉석 팔씨름 대회의 승자는?','두번째 소식은 무엇?','세번째 소식은 또 무엇?']

for idx, path in enumerate(paths):
    img = cv2.imread(path)
    fixedWidth = 0
    fixedHeight = 0

    mainWPos = 0
    mainHPos = 0

    if img.shape[1]/img.shape[0] > videoWidth/videoHeight:
        fixedWidth = videoWidth
        fixedHeight = round(videoWidth/fixedWidth * img.shape[0])
        mainWPos = 0
        mainHPos = round((videoHeight-fixedHeight) / 2)
    else:
        fixedHeight = videoHeight
        fixedWidth = round(videoHeight/img.shape[0] * img.shape[1])
        mainWPos = round((videoWidth-fixedWidth) / 2)
        mainHPos =0

    mainImg = img.copy()

    mainImg = cv2.resize(mainImg, (fixedWidth, fixedHeight))
    mainImg = cv2.resize(mainImg, (fixedWidth, fixedHeight))
    height, width, layers = mainImg.shape
    size = (videoWidth, videoHeight)

    overlay = img.copy()
    overlay = cv2.resize(overlay, (videoWidth, videoHeight))
    bg = cv2.blur(overlay, (30, 30))
    videoImg = combine_two_color_images_with_anchor(mainImg, bg, mainHPos, mainWPos)

    x, y, w, h = 0, videoHeight - 50, videoWidth, 50
    sub_img = videoImg[y:y + h, x:x + w]
    white_rect = numpy.ones(sub_img.shape, dtype=numpy.uint8) * 0
    res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

    # Putting the image back to its position
    videoImg[y:y + h, x:x + w] = res
    videoImg = combine_two_color_images_with_anchor(logoImg,videoImg,videoHeight-45,5)

    img_pil = Image.fromarray(videoImg)
    draw = ImageDraw.Draw(img_pil)
    draw.text((80, videoHeight - 35), description[idx], font=font, fill=(255, 255, 255, 100))
    videoImg = numpy.array(img_pil)
    frame_array.append(videoImg)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(pathOut, fourcc, fps, size)

for i in range(len(frame_array)):
    # writing to a image array
    out.write(frame_array[i])

out.release()
