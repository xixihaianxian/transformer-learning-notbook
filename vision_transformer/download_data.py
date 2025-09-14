import requests
import os
from loguru import logger
from pathlib import Path
from tqdm import tqdm
import zipfile
from typing import List, Tuple, Union, Any
import config
from urllib.parse import urljoin
import time
import threading
import random

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

def download_data(url:str,name:str=None,data_path:str=None,need_unpack:bool=True):
    r"""
    Download the file from the given file path to the specified path and unzip it.
    :param url: download url
    :param name: zip name
    :param data_path: zip root dir(压缩包根路径)
    :param need_unpack: Is it necessary to extract?
    :return:
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
    if need_unpack: # 判断是否需要解压压缩包
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

# Github加速组件
class GitHubAccelerator:
    def __init__(self):
        # 定义普通下载链接
        self.download_url=config.DOWNLOAD_URL
        # 定义raw下载链接
        self.raw_url=config.RAW_URL
    # 重写github下载的url
    def rewrite_github_url(self,original_url:str,node_type:str="download")->List[Tuple[str,str,str]]:
        # 判断链接是否是github内部的链接
        accelerated_urls = []
        if "github.com" not in original_url:
            raise ValueError(f"{original_url} not is a github url!")
        #判断下载类型
        nodes=self.download_url if node_type=="download" else self.raw_url
        # 构建极速下载的清单
        for node_url,countries,description in nodes:
            # 处理下载链接
            if node_type=="download":
                accelerated_url=original_url.replace(
                    "https://github.com",
                    node_url
                )
            # 处理raw链接
            elif node_type=="raw":
                if "/blob/" in original_url:
                    # accelerated_url=original_url.replace(
                    #     "https://github.com",
                    #     node_url
                    # ).replace("/blob/","/")
                    accelerated_url=urljoin(node_url,original_url)
                else:
                    accelerated_url=original_url.replace(
                        "https://github.com",
                        node_url
                    )
            else:
                accelerated_url=original_url
            accelerated_urls.append((accelerated_url,countries,description))
        return accelerated_urls
    # 测速
    def test_node_speed(self,url:str,timeout=5):
        logger.info(f"🔍 正在测试:{url}")
        try:
            start_time=time.time()
            # 定义请求头,根据自己的电脑来定义
            headers = {'User-Agent': 'Mozilla/5.0 (GitHub Accelerator Speed Test)'}
            response=requests.head(url=url,timeout=timeout,allow_redirects=True,headers=headers)
            if response.status_code==200:
                return time.time()-start_time
        # 测试失败返回None,表示超时
        except Exception as e:
            return None
    # 使用延迟最小的url来下载文件
    def get_fastest_node(self,accelerated_urls:List[Tuple[str,str,str]])-> List[str]:
        results=[]
        threads=[]
        # 获取可用的url
        # for accelerated_url,countries,description in accelerated_urls:
        #     speed=self.test_node_speed(accelerated_url)
        #     if speed is not None:
        #         results.append((accelerated_url,countries,description,speed))
        def test_speed_thread(url_desc):
            accelerated_url, countries, description=url_desc
            speed = self.test_node_speed(accelerated_url)
            if speed is not None:
                results.append((accelerated_url, countries, description, speed))
        # 多线程加速网站的检测
        for url_desc in accelerated_urls:
            thread=threading.Thread(target=test_speed_thread,kwargs={"url_desc":url_desc})
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        # 获取fastest node
        if results:
            results.sort(key=lambda x:x[3])
            results=list(map(lambda t:(t[0],t[1],t[2]),results))
            return results[0]
        else:
            return random.choice(accelerated_urls)
    # 下载
    def download_file(self,url_desc):
        accelerated_url, countries, description= url_desc
        logger.info(f"📍 正在使用{countries}的节点。")
        logger.info(f"🙏 感谢{description}。")
        download_data(url=accelerated_url)

if __name__=="__main__":
    original_url="https://github.com/PowerShell/PowerShell/releases/download/v7.5.3/powershell-7.5.3-linux-arm64.tar.gz"
    gitHub_accelerator=GitHubAccelerator()
    urls=gitHub_accelerator.rewrite_github_url(original_url)
    url_desc=gitHub_accelerator.get_fastest_node(urls)
    gitHub_accelerator.download_file(url_desc)