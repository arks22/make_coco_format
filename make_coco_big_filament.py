"""
$ python3 make_coco.py jpg_yyyy
"""

import os
import sys

import json
import collections as cl

import re

from tqdm import tqdm
import datetime

import collections as cl
import sunpy.net
from sunpy.net import hek
import astropy.io.fits as iofits

from shapely.geometry import Polygon


#ファイルの用意
args = sys.argv #コマンドラインからjsonにdumpするディレクトリの名前を受け取る

dirname = args[1]
if not re.compile('^jpg_[12][0-9]{3}').match(dirname): #名前がフォーマットと異なれば異常終了
    print("Specify the jpg directory in the format \"jpg_yyyy\".")
    sys.exit(1)

JPG_DIR_PATH  = os.path.abspath('./{}'.format(dirname))
JPG_FILES = os.listdir(JPG_DIR_PATH)

target='_'
idx = dirname.find(target)
YEAR = dirname[idx+1:]

FITS_DIR_PATH = os.path.abspath('./fits_{}'.format(YEAR))
if not os.path.exists(FITS_DIR_PATH): #fitsgが存在しなければ異常終了
    print("No such directory" + FITS_DIR_PATH);
    print("Create a directory of fits data corresponding to the target jpg directory.");
    sys.exit(1)



def images():
    tmps = []
    global image_ids
    image_ids = {}

    for i in range(len(JPG_FILES)):
        year = JPG_FILES[i][14:18]
        month = JPG_FILES[i][18:20]
        day = JPG_FILES[i][20:22]
        hour = JPG_FILES[i][23:25]
        minute = JPG_FILES[i][25:27]
        second = JPG_FILES[i][27:29]
        
        image_ids[JPG_FILES[i]] = JPG_FILES[i][14:22] + JPG_FILES[i][23:29]
        
        tmp = cl.OrderedDict()
        tmp["id"] = JPG_FILES[i][14:22] + JPG_FILES[i][23:29]
        tmp["file_name"] = JPG_FILES[i]
        tmp["width"] = 2048
        tmp["height"] = 2048
        tmp["date_captured"] = year + "-" + month + "-" + day +" " + hour + ":" + minute + ":" + second
        tmps.append(tmp)
    return tmps


def annotations():
    tmps = []
    all_polygons = make_polygons()

    for i in range(len(JPG_FILES)):
        for j in range(len(all_polygons[JPG_FILES[i]])):
            
            segmentation = []
            poly_x = []
            poly_y = []
            
            polygon = []
            
            for k in range(len(all_polygons[JPG_FILES[i]][j])):
                #print(all_polygons[JPG_FILES[i]][j][k])
                if not all_polygons[JPG_FILES[i]][j][k]=='':
                    segmentation.append(all_polygons[JPG_FILES[i]][j][k][0])
                    segmentation.append(all_polygons[JPG_FILES[i]][j][k][1])
                    poly_x.append(all_polygons[JPG_FILES[i]][j][k][0])
                    poly_y.append(all_polygons[JPG_FILES[i]][j][k][1])
                    
                    polygon.append((all_polygons[JPG_FILES[i]][j][k][0],all_polygons[JPG_FILES[i]][j][k][1]))
                    
            tmp = cl.OrderedDict()
            polygon = Polygon(polygon)

            if not ((poly_x == []) or (poly_y == [])) and not polygon.area<600:
                tmp_segmentation = cl.OrderedDict()
                tmp["segmentation"] = [segmentation]
                tmp["id"] = str(10**6*int(YEAR) + 10**3*i + j)
                tmp["image_id"] = str(image_ids[JPG_FILES[i]])
                tmp["category_id"] = 1
                
                #areaを作成するためにPoygon型に格納する
                polygon = Polygon(polygon)
                tmp["area"] = polygon.area
                tmp["iscrowd"] = 0
                tmp["bbox"] =  [min(poly_x), min(poly_y), max(poly_x)-min(poly_x), max(poly_y)-min(poly_y)]
            
                tmps.append(tmp)
    return tmps

    
def make_polygons():
    all_polygons = {}

    for i in tqdm(range(len(JPG_FILES))):
        polygons = []

        year = int(JPG_FILES[i][14:18])
        month = int(JPG_FILES[i][18:20])
        day = int(JPG_FILES[i][20:22])
        hour = int(JPG_FILES[i][23:25])
        minute = int(JPG_FILES[i][25:27])
        second = int(JPG_FILES[i][27:29])

        dt = datetime.datetime(year, month, day, hour, minute, second)

        client = hek.HEKClient()
        tstart = dt + datetime.timedelta(minutes=-3)
        tend = dt + datetime.timedelta(minutes=3)

        event_type = "FI"
        result = client.search(sunpy.net.attrs.Time(tstart,tend),hek.attrs.EventType(event_type))

        fts_path = FITS_DIR_PATH + "/" + JPG_FILES[i][0:-4]+ ".fts"
        if not os.path.exists(fts_path):
            print("No fts file: " + fts_path)

        list = iofits.open(fts_path)
        pic = list[0]
        header = pic.header
        data = pic.data

        for j in range(len(result)):
            polygon = []
            #print(result[j]['bound_chaincode'])
            polygon = result[j]['bound_chaincode']
            polygon = polygon[9:-2]
            polygon = polygon.split(',')
            for k in range(len(polygon)):
                #print(result[j]['event_starttime'])

                if not (polygon[k]==''): #print("No Polygons: " + JPG_FILES[i])
                    polygon[k] = polygon[k].split()
                    polygon[k][0] = float(polygon[k][0])+header['CRPIX1']
                    polygon[k][1] = -1 * float(polygon[k][1])+header['CRPIX2']
            polygons.append(polygon)

        all_polygons[JPG_FILES[i]] = polygons

    return all_polygons


def categories():
    tmps = []
    tmp = cl.OrderedDict()
    tmp["id"] = 1
    tmp["supercategory"] = "filament"
    tmp["name"] ="filament"
    tmps.append(tmp)
    
    return tmps


def info():
    tmp = cl.OrderedDict()
    tmp["description"] = "Filament mask dataset of " + YEAR
    tmp["year"] = YEAR
    tmp["contributor"] = "Sasaki Akira"
    tmp["data_created"] = str(datetime.datetime.now())

    return tmp


def licenses():
    tmp = cl.OrderedDict()
    tmp["id"] = 1
    tmp["url"] = "none"
    tmp["name"] = "administrater"
    tmp["items"] = "a"
    
    return tmp


def main():
    js = cl.OrderedDict()

    js["info"]        = info()    
    js["licenses"]    = licenses()
    js["images"]      = images()
    js["annotations"] = annotations()
    js["categories"]  = categories()

    jsonfilename = 'datasets_' + YEAR + '_bigfil.json'
    fw = open(jsonfilename,'w')
    json.dump(js,fw)
    print(jsonfilename + ' was created')
    
if __name__=='__main__':
    main()
