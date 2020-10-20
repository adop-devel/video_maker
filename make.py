__author__ = 'sunjung@adop.cc'

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir
import uuid
import re
import os
import numpy
import cv2
import json
import time
from PIL import ImageFont, ImageDraw, Image
import requests # 이미지 다운로드
import pymysql # mysql 다운르도
import boto3
import pymysql
import socket
import shutil

testVideo = 1

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


def setText(timg, color, alignment, videoHeight, desc, font):
    img_pil = Image.fromarray(timg)
    draw = ImageDraw.Draw(img_pil)
    draw.text((80, videoHeight - 55), desc, font=font, fill=color, align=alignment)
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

conn = pymysql.connect(
    host='insight-cluster-1.cluster-cnzcxy7quzcs.ap-northeast-2.rds.amazonaws.com'
    , user='adopadmin'
    , password='Adop*^14'
    , db='insight'
    , charset='utf8'
)
#i_recommand_video 에서 데이터 select
# cur = conn.cursor()
# sql_getRange = """
#             SELECT * FROM insight.i_news
#             where site_idx = 756 and  com_idx = 756
#             """
# cur.execute(sql_getRange)
# for i in cur:
#     print(i)


# 이미지 다운로드
# url ="https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/150px-Wikipedia-logo-v2.svg.png"
#
# r = requests.get(url)
# file = open("wiki_logo.jpg","wb")
# file.write(r.content)
# file.close()

def makeArticleVideo(data):
    global testVideo
    # strTestVideo = str(testVideo)
    # 이미지 폴더 초기화
    if( os.path.isfile("/Users/admin/git/video_maker/images/1.jpg")):
        os.remove("/Users/admin/git/video_maker/images/1.jpg")
        os.remove("/Users/admin/git/video_maker/images/2.jpg")
        os.remove("/Users/admin/git/video_maker/images/3.jpg")
        os.remove("/Users/admin/git/video_maker/images/4.jpg")
        os.remove("/Users/admin/git/video_maker/images/5.jpg")

#이미지 저장
    img_idx = 1
    for img_url in data["images"]:
        r = requests.get(img_url)
        file = open("images/"+str(img_idx)+".jpg","wb")
        file.write(r.content)
        file.close()
        img_idx = img_idx + 1



    # vidoe 설정
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
    # print("image paths = ", paths)

    logoPath = '%slogo' % VIDEO_MAKER_PATH
    logoPath = [os.path.join(logoPath, i) for i in os.listdir(logoPath) if re.search(".(jpg|png|gif)$", i)]
    paths.sort()
    # print("logo images = ", logoPath)

    introPath = '%sassets/adop-intro-1080.jpg' % VIDEO_MAKER_PATH

    # adop 이미지 크기 정의
    introImg = cv2.imread(introPath)
    introImg = cv2.resize(introImg, (videoWidth, videoHeight))

    # 타이틀 옆 로코 그기 정의
    logoImg = cv2.imread(logoPath[0])
    logoImg = cv2.resize(logoImg, (40, 40))

    # 여기에 타이틀 정보와 랜딩 url 이 있는것인가?
    # infoJsonPath = '%sdescription/info.json' % VIDEO_MAKER_PATH
    # with open(infoJsonPath) as json_file:
    #     vInfoData = json.load(json_file)
    #     print(type(vInfoData))
    #     print(" vInfoData = ", vInfoData)
    vInfoData = data

    # GUID 의 비디오명 생성
    firstTitle = vInfoData["firstTitle"]
    print("firstTitle = ",firstTitle)
    firstTitle = uuid.uuid1()
    firstTitle = str(firstTitle)
    firstTitleMP4 = "video_"+firstTitle+".mp4"
    firstTitlePath = firstTitle+"/"
    firstTitleGroup = "group_"+firstTitle
    firstTitleItem = "item+_"+firstTitle

    vInfoData["firstTitleMP4"] = firstTitleMP4
    vInfoData["firstTitlePath"] = firstTitlePath
    vInfoData["firstTitleGroup"] = firstTitleGroup
    vInfoData["firstTitleItem"] = firstTitleItem

   # 비디오 설정
    pathOut = '%svideo/news%s.mp4' % (VIDEO_MAKER_PATH, firstTitle)
    fps = 15
    frame_array = []

    description = vInfoData['description']
    fontType = vInfoData['font']

    fontpath = "%sfonts/%s.otf" % (VIDEO_MAKER_PATH, fontType)
    font = ImageFont.truetype(fontpath, int(vInfoData['font_size']))

    # 비디오 만들기 (사진이동 + fadein/out)
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
            # videoImg = combine_images_with_anchor(logoImg, videoImg, videoHeight - 65, 5)

            croppedImg = videoImg[0:videoHeight, 0:videoWidth]
            croppedImg = setText(croppedImg, vInfoData['font_color'], vInfoData['alignment'], videoHeight, description[idx], font)

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
    # print("strTestVideo = "+strTestVideo)
    # 비디오 폴더 초기
    if (os.path.isfile("/Users/admin/git/video_maker/video") ):
        shutil.rmtree("/Users/admin/git/video_maker/video") # 디렉토리 + 안에 있는 파일도 삭제
        os.mkdir("/Users/admin/git/video_maker/video")

    finalMakeTask = "ffmpeg -i %svideo/news%s.mp4 -vcodec libx264 %svideo/video_%s.mp4" % (VIDEO_MAKER_PATH, firstTitle, VIDEO_MAKER_PATH, firstTitle)
    os.system(finalMakeTask)
    finalVideoTask = "chmod 777 %svideo/video_%s.mp4" % (VIDEO_MAKER_PATH , firstTitle )
    os.system(finalVideoTask)

    testVideo = testVideo + 1

    # data 에 DB 에 넣을 데이터 추가

    return vInfoData


## 여기까지가

def addToS3Atomvideo(videoInfoData):
    session = boto3.Session(profile_name='AMW')
    videoS3 = session.resource('s3')
    # videoS3 = boto3.resource('s3')
    videoPath = "video/"+videoInfoData["firstTitleMP4"]
    print("videoPath = ",videoPath)

    s3Path = "advideo/"+videoInfoData["firstTitlePath"]+videoInfoData["firstTitleMP4"]
    print("s3Path = ",s3Path)
    videoS3.meta.client.upload_file(videoPath, 'adop-atom-video', s3Path, ExtraArgs={'ACL':'public-read' ,'ContentType':'video/mp4'} )
    return videoInfoData
def insertDataToAtomDB(videoInfoData):
    # uuidtestData = 'allentestsite.co.kr'
    # uuiddata = uuid.uuid3(uuid.NAMESPACE_URL,uuidtestData)
    # uuiddata = str(uuiddata)
    # print("uuiddata = ",uuiddata)

    # uuiddataMP4 = uuiddata+".mp4"
    # uuidtestPath = uuiddata+"/"
    # uuidtestGroup = "group_"+uuiddata
    # uuidtestItem = "item+"+uuiddata


    try:
        conn_atom = pymysql.connect(
            host='compass-slave.cnzcxy7quzcs.ap-northeast-2.rds.amazonaws.com'
            , user='adopadmin'
            , password='Adop*^14'
            , db='atom'
            , charset='utf8'
        )

        cur_atom = conn_atom.cursor()

        sql_insertItemGroupInfo = """
            INSERT INTO atom.a_item_group_info 
                (com_idx, group_idx, user_idx, item_group_name, item_group_name_chk, 
                item_group_clk_url, item_group_clk_url_chk, item_group_clk_url_reject_type, 
                item_group_clk_url_reject_memo, item_group_chk_status, item_group_rechk_yn, 
                item_group_allpass_yn, item_group_chk_adop, item_group_ad_type, 
                item_group_reg_date, item_group_update_date, item_group_chk_date, 
                item_group_del_yn, item_group_upload_type, item_group_bg_color, 
                item_group_alt, item_group_attr)
            VALUES ( 1, 422, 1802, %s, 'Y', 'article', 'Y', 'R', 'article', 
                'N', 'N', 'N', 'N', 'V', now(), now(), null, 'N', 'u', '','', '')
        """
        itemGroupNameTest = "AllenWebsite20201020-4"
        cur_atom.execute(sql_insertItemGroupInfo, (videoInfoData["firstTitle"]) )
        conn_atom.commit()
        # 마지막 insert id 가져오기 - 근데 막약 내가 넣고 그사이에 다른 사람이 넣으면 어떻게 되는건가? 내 conn 으로 넣은것만?
        atom_lastrowid =  cur_atom.lastrowid
        print(" conn_atom.insert_id = ", atom_lastrowid )


        sql_insert_aItemInfo = """
            INSERT INTO atom.a_item_info 
                (item_group_idx, com_idx, group_idx, user_idx, item_name, 
                item_clk_url, item_file_name, item_file_path, item_file_chk, 
                item_end_url, item_reject_memo, item_reject_type, item_size, 
                item_type, item_reg_date, item_update_date, item_del_yn, 
                item_endcard_type, item_endcard_idx)
            VALUES (%s, 1, 422, 1802, %s, '',
             %s, %s,
              'R', '', NULL, NULL, 'article', 'K',
               now(), now(), 'N', '', NULL)
        """
        myItemName = 'allenTestItem20201020-3'
        myItemFileName = "allen3_f4aa43270dd1a9750d379cf201762692.mp4"
        myItemFilePath = "dirAllen3_f4aa43270dd1a9750d379cf201762692/"
        cur_atom.execute(sql_insert_aItemInfo, (atom_lastrowid, videoInfoData["firstTitleItem"],videoInfoData["firstTitleMP4"], videoInfoData["firstTitlePath"] ))
        atom_lastrowid2 =  cur_atom.lastrowid
        print("2. conn_atom.insert_id = ", atom_lastrowid2 )
        conn_atom.commit()

        data["com_idxs"] = comIdx_array
        data["site_idxs"] = siteIdx_array
        data["description"] = desc_array
        data["link_arrays"] = link_array
        data["images"] = imgSrc_array
        data["news_ids"] = newsId_array

        for i in range(len(videoInfoData["news_ids"])):
            sql_insert_aArticleVideoInfo = """
            insert into atom.a_article_video_info
                (item_idx, font, font_size, font_color, alignment, article_size,
                 article_subtitle, article_landing_url, article_img_path, article_logo_path )
                values 
                ( %s, 'dotum', 20, '#000000', 'left', 480, %s,
                 %s, %s, %s)
    
            """
            # base64 값 필요
            convertedTitle = "testallen64"
            landing_url = "test.com"
            img_path = "test.jpg"
            logo_path = "logotest.jpg"
            cur_atom.execute(sql_insert_aArticleVideoInfo, (atom_lastrowid2, videoInfoData["description"][i], videoInfoData["link_arrays"][i], videoInfoData["images"][i] , logo_path ))
            atom_lastrowid3 = cur_atom.lastrowid
            print("2. conn_atom.insert_id = ", atom_lastrowid3 )


        conn_atom.commit()

    except Exception as e:
        print( "error = ",e)
    finally:
        conn_atom.close()
        return True


# print(" 이게 먼저 끝나지는 않겠지?")



# hostname = socket.gethostname() # hostname 은 무엇있가?
conn = pymysql.connect(
    host='insight-cluster-1.cluster-cnzcxy7quzcs.ap-northeast-2.rds.amazonaws.com'
    , user='adopadmin'
    , password='Adop*^14'
    , db='insight'
    , charset='utf8'
)

cur = conn.cursor()

sql_getRange = """
            SELECT * FROM insight.i_recommend_video_site WHERE del_yn = 'N'
            """
cur.execute(sql_getRange)
# comIdxs = []
# siteIdxs = []
medias = []
for i in cur:
    mediaDic = {}
    mediaDic["com_idx"] = i[1]
    mediaDic["site_idx"] = i[2]
    mediaDic["news_id"] = i[3]
    medias.append(mediaDic)

    # comIdxs.append(i[1])
    # siteIdxs.append(i[2])

# print("comIdxs", comIdxs)
# print("siteIdxs", siteIdxs, '\n')

# 기존에 몇번재 기사까지 영상으로 만들었는지 체크하기 위한 idx 값은 어디서 체해야하는가?

sql_getNewsData = """
            SELECT com_idx, site_idx, title, link, image_url, news_id FROM insight.i_news
            where com_idx = %s and  site_idx = %s 
            """
# AND news_id >= %s # 이부분을 살려야 한번 만든 기사는 동영상으로 만들지 않는다.
index = 0
for j in range(len(medias)):
    # print(medias[j]["com_idx"])
    # print(" ")
    cur.execute(sql_getNewsData, (medias[j]["com_idx"], medias[j]["site_idx"]
                                  # , medias[j]["news_id"]
                                  ))

    articleRows = cur.fetchall()

    articleVideoBufferArray = []
    # 여기서 cur 에 있는 각 기의 데이터를 5개씩 쪼개서 영상을 만들면 된다.
    articleLen = len(articleRows)
    print("articleLen = ",articleLen)
    videoCount = articleLen//5
    print(" videoCount = ", videoCount)
    convertedArticleCount = ( 5*videoCount )

    print(articleRows[convertedArticleCount-1] )
    lastArticleNewsId = articleRows[convertedArticleCount-1][5] # 마지막 news_idx
    lastAtricleComIdx = articleRows[convertedArticleCount-1][0]
    lastAtricleSiteIdx = articleRows[convertedArticleCount-1][1]


    articleVideoBuffer = [] # 하나의 비디오를만ㄷ르기위한 데이터 단
    for i in range(convertedArticleCount):
        # 5개씩 하나의 묶음을 만든다.
        articleVideoBuffer.append(articleRows[i])
        if ( (i+1)%5 == 0 ):
            articleVideoBufferArray.append(articleVideoBuffer) # 이렇게 할 경우 5개 미만이 모인 aricleVideoBuffer 는 버려진다.
            articleVideoBuffer = []
        # if( i+1 == articleLen):
        #     break

    #여기까지 실행되면 몇개의 기사비디오를 만들 수 있는 지 알 수 있다 = len(articleVideoBufferArray)

    # article 비디오 버퍼에는 기사데이터가 5개찍 들어가 있다.
    print("### articleVideoBufferArray .length = ",len(articleVideoBufferArray))
    for oneBuffer in articleVideoBufferArray:
        # print(oneBuffer)
        data = {
            "font": "gothic",
            "font_size": "14",
            "font_color": "#FFFFFF",
            "alignment": "left",
        }
        # com_idx, site_idx, title, link, image_url, news_id
        comIdx_array = []
        siteIdx_array = []
        desc_array = []
        link_array = []
        imgSrc_array = []
        newsId_array = []
        for oneArticle in oneBuffer:
            comIdx_array.append(oneArticle[0])
            siteIdx_array.append(oneArticle[1])
            desc_array.append(oneArticle[2])# 타이틀으 가져온다.y
            link_array.append(oneArticle[3])
            imgSrc_array.append(oneArticle[4])
            newsId_array.append(oneArticle[5])

        data["com_idxs"] = comIdx_array
        data["site_idxs"] = siteIdx_array
        data["description"] = desc_array
        data["link_arrays"] = link_array
        data["images"] = imgSrc_array
        data["news_ids"] = newsId_array
        data["firstTitle"] = desc_array[0]
        # json_data = json.dumps(data)
        # print("data = ",data,"\n")
        # print("=-=-=-=-=-=-=-")
        v_data = makeArticleVideo(data)
        v_data = addToS3Atomvideo(v_data)
        result = insertDataToAtomDB(v_data)
        print("restul = ",result)


        # 동영상으로 만든 마지막 기사의 news_id를 i_recommend_news 의 new_id 에 저
        sql_updateNewsId = """
            UPDATE i_recommend_video_site
            SET new_id = %s
            WHERE com_idx = %s
            AND site_idx = %s
        """
        cur.execute( sql_updateNewsId, (lastArticleNewsId, lastAtricleComIdx, lastAtricleSiteIdx))
        conn.commit()


conn.close()