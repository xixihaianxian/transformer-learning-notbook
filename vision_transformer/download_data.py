import requests
import os
from loguru import logger
from pathlib import Path
from tqdm import tqdm

def download_data(url:str,name:str=None,data_path:str=None):
    r"""
    Download the file from the given file path to the specified path and unzip it.
    :return: data path
    """
    # 判断是name是否提前定义
    if name is not None:
        pass
    else:
        name=os.path.basename(url)
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
        "http": "http://127.0.0.1:7890",
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
if __name__=="__main__":
    download_data(url="https://github.com/mrdbourke/pytorch-deep-learning/raw/main/data/pizza_steak_sushi.zip")