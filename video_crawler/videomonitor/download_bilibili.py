#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/home/monitor/opt/video_data/')
from resource.http import HTMLResource, JsonResource
from resource.database import DataBase
from resource.util import Util
from bilibili import Bilibili
import os
import threadpool
import datetime
import traceback

image_base_path = "/media/3mage/"
video_base_path = "/media/3mage/video/"
site = 'bilibili'
Bad_Datas = []
headers = Bilibili().get_headers()

def download_video(para):
    _id, cid, date_str = para
    try:
        idstr = str(_id)
        print idstr
        cidstr = str(cid)
        video_path = video_base_path+site+'/'+date_str + '/' + cidstr + '.flv'
        jpgdir = image_base_path+site+'/'+date_str + '/' + cidstr + '/'
        jpg_path = jpgdir + cidstr + '_20.jpg'
        jpg_path1 = jpgdir + cidstr + '_5.jpg'
        if not os.path.exists(jpg_path1):
            video_url_cdn = Bilibili().parse(cidstr)
            if video_url_cdn[0] == '-':
                status = video_url_cdn
                Bad_Datas.append([idstr, '', status])
                return None
            if len(video_url_cdn) == 0:
                size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*25)
            else:
                size = HTMLResource('', headers=headers).download_video_ts(video_url_cdn, video_path, 1024*1024*35)
            if size is not None and size > 0:
                # jpgdir = image_base_path+site+'/'+date_str + '/' + idstr + '/'
                returncode = Util.movie_split_image(video_path, jpgdir, cidstr)
                if os.path.exists(jpg_path):
                    DataBase.update_data(site, idstr, date_str)
                else:
                    if len(video_url_cdn) == 0:
                        size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*50)
                    else:
                        size = HTMLResource('', headers=headers).download_video_ts(video_url_cdn, video_path, 1024*1024*70)
                    if size is not None and size > 0:
                        returncode = Util.movie_split_image(video_path, jpgdir, cidstr)
                        if os.path.exists(jpg_path):
                            DataBase.update_data(site, idstr, date_str)
                        elif os.path.exists(jpg_path1):
                            DataBase.update_data(site, idstr, date_str, '1')
                        else:
                            print('remove bad jpg dir: ' + jpgdir)
                            for file in os.listdir(jpgdir):
                                os.remove(os.path.join(jpgdir, file))
                            os.removedirs(jpgdir)
                            Bad_Datas.append([idstr, '', '-98'])
            else:
                Bad_Datas.append([idstr, '', '-99'])
            if os.path.exists(video_path):
                os.remove(video_path)
    except Exception as e:
        print e
        traceback.print_exc()
        print _id


def download():
    runday = datetime.date.today()
    exe_time = datetime.datetime.now()
    print runday
    data_list = DataBase.get_new_ciddatas(site)
    count = len(data_list)
    if count > 1000:
        del data_list[1000:]
        count = len(data_list)
    if count >= 20:
        print count
        i = 0

        para_list = data_list
        hour = str(exe_time.hour)
        if len(hour)==1:
            hour = '0' + hour
        date_str = runday.strftime('%Y%m%d') + hour
        print date_str
        videodir = video_base_path+site+'/'+date_str
        jpgdir = image_base_path+site+'/'+date_str
        if not os.path.exists(jpgdir):
            os.makedirs(jpgdir)
        if not os.path.exists(videodir):
            os.makedirs(videodir)

        for para in para_list:
            para[2] = date_str
        pool_size = 8
        pool = threadpool.ThreadPool(pool_size)
        requests = threadpool.makeRequests(download_video, para_list)
        [pool.putRequest(req) for req in requests]
        pool.wait()
        pool.dismissWorkers(pool_size, do_join=True)
        del para_list[0: len(para_list)]
        DataBase.update_datas(site, Bad_Datas)
        del Bad_Datas[0: len(Bad_Datas)]

        Util.delete_empty_dir(jpgdir)
        if os.path.exists(jpgdir):
            DataBase.insert_pathdata(site, image_base_path, date_str)


def download_by_day():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    runday = datetime.date(2015,9,25)
    days = (today - runday).days + 1
    print runday
    data_list, bad_data_list = DataBase.get_ciddatas(site, 'status=0 and video_type="vupload"')

    datas = []
    count = len(data_list)
    print data_list[-1]
    print count

    print len(bad_data_list)
    for bad_data in bad_data_list:
        datas.append([str(bad_data[0]), '', '-1'])
    DataBase.update_datas(site, datas)
    del datas[0: len(datas)]

    repeat_cids = set()
    repeat_cid_list = []
    for data in data_list:
        cid = data[1]
        if cid in repeat_cids:
            repeat_cid_list.append(data)
        else:
            repeat_cids.add(cid)
    print len(repeat_cid_list)
    for repeat_cid in repeat_cid_list:
        datas.append([str(repeat_cid[0]), '', '-9'])
    DataBase.update_datas(site, datas)
    del datas[0: len(datas)]
    del repeat_cid_list[0: len(repeat_cid_list)]
    repeat_cids.clear()

    base_count = ((count - 1) / days) + 1
    print base_count
    para_list = []
    i = 0
    while(i < count):
        para_list.append(data_list[i])
        i += 1
        if i % base_count == 0 or i >= count:
            date_str = runday.strftime('%Y%m%d')
            print date_str
            videodir = video_base_path+site+'/'+date_str
            jpgdir = image_base_path+site+'/'+date_str
            if not os.path.exists(jpgdir):
                os.makedirs(jpgdir)
            if not os.path.exists(videodir):
                os.makedirs(videodir)
            # _id, sid, date_str
            for para in para_list:
                para[2] = date_str
            pool_size = 8
            pool = threadpool.ThreadPool(pool_size)
            requests = threadpool.makeRequests(download_video, para_list)
            [pool.putRequest(req) for req in requests]
            pool.wait()
            pool.dismissWorkers(pool_size, do_join=True)
            del para_list[0: len(para_list)]
            DataBase.update_datas(site, Bad_Datas)
            del Bad_Datas[0: len(Bad_Datas)]
            Util.delete_empty_dir(jpgdir)
            if os.path.exists(jpgdir):
                if len(os.listdir(jpgdir)) > (base_count/2) or i >= count:
                    DataBase.insert_pathdata(site, image_base_path, date_str)
                    runday = runday + oneday

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # download()  3705961
    download_by_day()