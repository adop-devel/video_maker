import pymysql
import requests
import socket
import json

# hostname = socket.gethostname() # hostname 은 무엇있가?
conn = pymysql.connect(
    host='insight-cluster-1.cluster-cnzcxy7quzcs.ap-northeast-2.rds.amazonaws.com'
    , user='adopadmin'
    , password='Adop*^14'
    , db='insight'
    , charset='utf8'
)

# # 필터 상테를 가져온다.
# with conn.cursor(pymysql.cursors.DictCursor) as curs:
#     sql_getRange = """
#             SELECT * FROM insight.i_news
#             where site_idx = 756 and  com_idx = 756
#             """
#     curs.execute(sql_getRange, hostname)
#     rows = curs.fetchall()
#     print(rows)

cur = conn.cursor()
# sql_getRange = """
#             SELECT * FROM insight.i_news
#             where site_idx = 756 and  com_idx = 756
#             """
sql_getRange = """
            SELECT * FROM insight.i_recommend_video_site WHERE del_yn = 'N'
            """
cur.execute(sql_getRange)
comIdxs = []
siteIdxs = []
for i in cur:
    # print(i[1])
    # print( i['com_idx'] )
    # print( i['site_idx'] )
    # print( i['new_id'] )
    # print( i['del_yn'] )
    comIdxs.append(i[1])
    siteIdxs.append(i[2])

print("comIdxs", comIdxs)
print("siteIdxs", siteIdxs, '\n')
# 기존에 몇번재 기사까지 영상으로 만들었는지 체크하기 위한 idx 값은 어디서 체해야하는가?

sql_getNewsData = """
            SELECT com_idx, site_idx, title, link, image_url FROM insight.i_news
            where com_idx = %s and  site_idx = %s
            """
index = 0
for j in range(len(comIdxs)):
    print(comIdxs[j])
    print(" ")
    cur.execute(sql_getNewsData, (comIdxs[j], siteIdxs[j]))

    articleRows = cur.fetchall()

    articleVideoBufferArray = []
    # 여기서 cur 에 있는 각 기의 데이터를 5개씩 쪼개서 영상을 만들면 된다.
    articleLen = len(articleRows)
    articleVideoBuffer = [] # 하나의 비디오를만ㄷ르기위한 데이터 단
    for i in range(articleLen):
        # 5개씩 하나의 묶음을 만든다.
        articleVideoBuffer.append(articleRows[i])
        if ( (i+1)%5 == 0 ):
            articleVideoBufferArray.append(articleVideoBuffer) # 이렇게 할 경우 5개 미만이 모인 aricleVideoBuffer 는 버려진다.
            articleVideoBuffer = []
        if( i+1 == articleLen):
            break
    #여기까지 실행되면 몇개의 기사비디오를 만들 수 있는 지 알 수 있다 = len(articleVideoBufferArray)

    # article 비디오 버퍼에는 기사데이터가 5개찍 들어가 있다.

    for oneBuffer in articleVideoBufferArray:
        # print(oneBuffer)
        data = {
            "font": "gothic",
            "font_size": "14",
            "font_color": "#000000",
            "alignment": "left",
        }
        desc_array = []
        imgSrc_array = []
        for oneArticle in oneBuffer:
            desc_array.append(oneArticle[2])# 타이틀으 가져온다.
            imgSrc_array.append(oneArticle[4])

        # 이미지 저장
        # img_url = i[4]
        # r = requests.get(img_url)
        # file = open("wiki_logo.jpg","wb")
        # file.write(r.content)
        # file.close()


        data["description"] = desc_array
        data["images"] = imgSrc_array
        # json_data = json.dumps(data)
        print("data = ",data,"\n")
        print("=-=-=-=-=-=-=-")
        # print(json_data['images'].__len__())
        img_idx = 1;
        for img_url in data["images"]:
            r = requests.get(img_url)
            file = open(str(img_idx)+".jpg","wb")
            file.write(r.content)
            file.close()
            print
            break




conn.close()