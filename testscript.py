"""Qiuby Zhukhi 2020"""
from simplekml import Kml
from subprocess import Popen, PIPE, STDOUT
from shutil import move as pindah
from os import path, makedirs, scandir, remove, sep
from sys import argv
from threading import Thread
from queue import Queue
from tqdm import tqdm
from json import loads

placemark = Kml()
kmz_placemark = Kml()
titik_files = Kml()
list_photo_no_coordinate = []
list_photo_yes_coordinate = []
numb_foto_koordinat = 0
numb_tidak_ada = 0
total = None

def confPath(mypath):
    last_element = mypath.split("\\")[-1]
    dict = {
        "last_element" : last_element,
        "titik_direct": f"{mypath}/link_foto_langsung_{last_element}.kml",
        "titik_kmz": f"{mypath}/link_foto_file_{last_element}.kml",
        "kompilasi_kmz": f"{mypath}/kompilasi_{last_element}.kmz"
    }
    return dict

def Konfigurasi():
    set_dict = {
        "add_jpg_to_kmz":False,
        "move_files_no_coordinate":True,
        "no_coordinate_folder":"NO COORDINATE",
        "view_photo_no_coordinate":False,

        "activate_titik_direct":True,
        "activate_titik_kmz":True,
        "activate_kompilasi_kmz":False,
        "show_result":False
    }
    return set_dict

def html_generator(**params):
    des = f'<![CDATA[<img style="max-width:300px;" src="file:///{params.get("directory_file")}">'
    if(params):
        for k, v in params.items():
           des += f'<p><span style="color: rgb(0, 0, 0);">{k}&nbsp;</span>: {v}</p>'
    des += "]]>"
    return des

def myplacemark(nama=None, directory_file=None, kordinat=None):
    des = f'<![CDATA[<img style="max-width:300px;" src="file:///{directory_file}">]]>'
    # des = f'<![CDATA[<img style="max-width:300px;" src="file:///{directory_file}">' \
    #       f'<p><font color="red">Image Description: </font></p>' \
    #       f'<p><span style="color: rgb(209, 72, 65);">Description</span>: <span style="color: rgb(41, 105, 176);"></span></p>]]>'
    #des = html_generator(directory_file=directory_file, )
    pl = placemark.newpoint(name=nama,
                            coords=kordinat,
                            description=des)
    pl.style.iconstyle.scale = 0.5
    pl.labelstyle.scale = 0

def real_path(file_name):
    return path.dirname(path.abspath(__file__)) + file_name

def Mycmd(cmd=None):
    prosess = Popen(
        cmd, stdout=PIPE, stderr=STDOUT, shell=True
    )
    return prosess

def getGPSPostion(tooldir=real_path("/tools/exiftool.exe"), input_files=None):
    cmd = f'"{tooldir}" -j -n "{input_files}"'
    cmd,_ = Mycmd(cmd).communicate()
    return dict(loads(cmd)[0])

def run_fast_scandir(dir, ext):  # Source func From: https://stackoverflow.com/a/59803793
    subfolders, files = [], []
    for f in scandir(dir):
        if f.is_dir():
            subfolders.append(f.path)
        if f.is_file():
            if path.splitext(f.name)[1].lower() in ext:
                files.append(f.path)

    for dir in list(subfolders):
        sf, f = run_fast_scandir(dir, ext)
        subfolders.extend(sf)
        files.extend(f)
    return subfolders, files

def makedir(target_Files=None, toDir=None):
    try:
        makedirs(name=f"{toDir}", exist_ok=True)
        pindah(target_Files, toDir)
        if(Konfigurasi().get("show_result")):
            print(f"Move: {target_Files}\n To: {toDir}\r\n")
    except Exception as e:
        # Permasalahan ketika file sudah ada didalam folder Coordinate
        # Autau terkait dengan pemindahan file ke folder coordinate
        # autoHapus
        remove(target_Files)


def KMZFiles(name=None, kordinat=None, directory_file=None, file_name=None, add_photo=Konfigurasi().get("add_jpg_to_kmz")):
    kmz_placemark.newpoint(name=name,
                           coords=kordinat,
                           description=f'<img style="max-width:300px;" src="files/{file_name}">')
    kmz_placemark.style.iconstyle.scale = 0.5
    kmz_placemark.labelstyle.scale = 0
    if (add_photo):
        placemark.addfile(directory_file)

def titik_file(name=None, kordinat=None, file_name=None):
    t = titik_files.newpoint(name=name,
                         coords=kordinat,
                         description=f'<img style="max-width:300px;" src="files/{file_name}">')
    t.style.iconstyle.scale = 0.5
    t.labelstyle.scale = 0

def kml_pilihan(**params):
    nama = params.get("nama")
    directory_file = params.get("directory_file")
    kordinat = params.get("kordinat")
    sett = Konfigurasi()
    if (sett.get("activate_titik_direct")):
        myplacemark(nama=nama, directory_file=directory_file, kordinat=kordinat)
    if (sett.get("activate_titik_kmz")):
        titik_file(name=nama, kordinat=kordinat, file_name=nama)
    if (sett.get("activate_kompilasi_kmz")):
        KMZFiles(name=nama, kordinat=kordinat, directory_file=directory_file, add_photo=Konfigurasi().get("add_jpg_to_kmz"))

def save_files_kml(path, sett=Konfigurasi()):
    path = confPath(path)
    try:
        if (numb_foto_koordinat > 0):
            if (sett.get("activate_titik_direct")):
                placemark.save(path.get("titik_direct"))
            if (sett.get("activate_titik_kmz")):
                titik_files.save(path.get("titik_kmz"), format=False)
            if (sett.get("activate_kompilasi_kmz")):
                kmz_placemark.save(path.get("kompilasi_kmz"))
            logs(path, sett)
    except Exception as e:
        print(e)
        print(path)

def getstarted(list_path):
    global numb_tidak_ada, numb_foto_koordinat, total
    sett = Konfigurasi()
    show_result = sett.get("show_result")
    if (sett.get("no_coordinate_folder") not in list_path):
        details_foto = getGPSPostion(input_files=list_path)
        coordinates = details_foto.get("GPSPosition")
        if (coordinates):
            numb_foto_koordinat += 1
            file_name = details_foto.get("FileName")
            lat,long = coordinates.split(" ")
            if(show_result):
                print(f"Membuat Placemark {file_name}")
                print(f"Koordinate: {lat}, {long}")
            kml_pilihan(nama=file_name, kordinat=[(long, lat)], directory_file=list_path)
            list_photo_yes_coordinate.append(list_path)
        else:
            if (show_result):
                print(f"Not Found GPS in: {list_path}")
            numb_tidak_ada += 1
            list_photo_no_coordinate.append(list_path)
            if (sett.get("move_files_no_coordinate")):
                link_moved = list_path[:list_path.rfind("\\") or list_path.rfind("/")]
                makedir(target_Files=list_path, toDir=f"{link_moved}/" + sett.get("no_coordinate_folder"))
    total = numb_tidak_ada + numb_foto_koordinat

def logs(mypath, settings):
    pathku = mypath.get("last_element")
    simpanan = f"FOLDER: {pathku}\r\n"\
               f"FOTO BERKOORDINAT: {numb_foto_koordinat}\r\n"\
               f"TIDAK ADA KOORDINAT: {numb_tidak_ada}\r\n"\
               f"TOTAL SEMUA FOTO: {total}"
    with open(mypath.get("titik_direct").replace(".kml", ".txt"), "w") as catatan:
        catatan.write(simpanan.replace("\r", "") if numb_tidak_ada == 0 else simpanan.replace("\r", "")+"\n"+f"LIST FOTO TAK BERKOORDINAT:\n" + "\n".join([i for i in list_photo_no_coordinate])+"\r\n\r\n")
        catatan.close()
    print(simpanan)

def main(mypath):
    kills = Queue()
    subfolders, files = run_fast_scandir(mypath, [".jpg"])
    print(f"FOTO TERDETEKSI: {len(files)}")
    for foto in tqdm(files, desc="Loading"):
        if Konfigurasi().get("no_coordinate_folder") not in files:
            t = Thread(target=getstarted, args=(foto, ))
            kills.put(t)
            t.setDaemon(True)
            t.start()
    for _ in tqdm(range(kills.qsize()), desc="KILL thread"):
        kills.get().join()
    save_files_kml(mypath)

def main_menu():
    #    tes = "E:\\testings"
    Mycmd("clear")
    tes = input("Path Foto: ")
    main(tes)
    # Handle Terminal executable
    ask = input("Press Any Keys To Exit: ")

def settings_args():
    try:
        news = path.abspath(__name__).replace("\__main__", "")
        main(news)

        #Kira2 ga ada code yang lain ga yah? masa gw harus replace __main__ nya ?? wkwkwkwkw
    except Exception as e:
        print(e)
    finally:
        input("Enter to Exit: ")
if __name__ == '__main__':
    settings_args()