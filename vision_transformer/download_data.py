import requests
import os
from loguru import logger
from pathlib import Path
from tqdm import tqdm
import zipfile
from typing import List

def recursive_unzip(zip_name:str,unpack_path:str):
    r"""
    :param zip_name: 压缩包名称
    :param unpack_path: 解压目标路径
    :return: None
    """
    # 判断目录是否存在
    if not os.path.exists(unpack_path):
        # raise FileExistsError(f"{unpack_path} not is exists.")
        os.makedirs(unpack_path,exist_ok=True)
    # 判断压缩包是否存在
    if not os.path.exists(zip_name):
        raise FileExistsError(f"{zip_name} not is exists.")
    # 将根目录解压
    with zipfile.ZipFile(zip_name,"r") as zip_ref:
        zip_ref.extractall(unpack_path)
    # 对解药压之后的目录进行遍历
    for root,dirs,files in os.walk(unpack_path):
        for file in files:
            next_zip_name=os.path.join(root,file)
            if zipfile.is_zipfile(next_zip_name):
                next_unpack_path=os.path.splitext(next_zip_name)[0]
                recursive_unzip(next_zip_name,next_unpack_path)
    # 解压成功日志
    logger.info(f"unpack successful!")

def download_data(url:str,name:str=None,data_path:str=None):
    r"""
    Download the file from the given file path to the specified path and unzip it.
    :return: data path
    """
    # 判断是name是否提前定义
    if name is not None:
        pass
    else:
        name=os.path.basename(url) # 获取压缩包的名称，包含压缩包类型
    # 判断data_path是否定义
    if data_path is None:
        data_path="data"
    # 创建文件夹
    if not os.path.exists(data_path):
        logger.info(f"Create {os.path.join(os.getcwd(),data_path)}")
    data_dir=os.path.join(os.getcwd(),data_path)
    os.makedirs(data_dir,exist_ok=True)
    # 设置代理
    proxies = {
        "http": "http://127.0.0.1:7890", # 这里替换成你代理的端口号
        "https": "http://127.0.0.1:7890",
    }
    zip_path=os.path.join(data_dir,name)
    # 获取数据
    response = requests.get(url, stream=True, proxies=proxies)
    # 获取数据长度
    file_size = int(response.headers.get("Content-Length"))
    # 下载数据到data_path
    with open(zip_path,"wb") as f,tqdm(
        total=file_size,
        unit="B",
        unit_divisor=1024,
        unit_scale=True,
    ) as bar: # 设置进度条
        logger.info(f"Downloading {data_path}")
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                bar.update(1024)
    # 压缩类型
    compression_formats = [
        "zip",
        "7z",
        "rar",
        "tar",
        "tgz",
        "tbz2",
    ]
    # 解压数据
    try:
        compress_type=name.split(sep=".")[1] # 获取压缩类型
        zip_name=name.split(sep=".")[0] # 获取要解压到文件的名称
        unpack_path=os.path.join(data_dir,zip_name) # 解压到文件的路径
        if compress_type in compression_formats:
            recursive_unzip(zip_path,unpack_path)
        else:
            raise ValueError
    except IndexError as e:
        logger.warning(f"Not find compress file.")
    except ValueError as e:
        logger.warning(f"Not find compress type.")
if __name__=="__main__":
    download_data(url="https://github.com/mrdbourke/pytorch-deep-learning/raw/main/data/pizza_steak_sushi.zip")