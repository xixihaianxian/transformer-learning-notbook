import requests
import os
from loguru import logger
from pathlib import Path
from tqdm import tqdm
import zipfile
import tarfile
import rarfile
from typing import List, Tuple, Union, Any
import config
from urllib.parse import urljoin
import time
import threading
import random
import re
import subprocess
from urllib import parse
import argparse

# 解压zip模块
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
    # zip压缩包的解压
    if zipfile.is_zipfile(zip_name):
        with zipfile.ZipFile(zip_name,"r") as zip_ref:
            zip_ref.extractall(unpack_path)
    # tar压缩包解压
    elif tarfile.is_tarfile(zip_name):
        with tarfile.open(zip_name,mode="r:*") as tar_ref:
            tar_ref.extractall(unpack_path)
    # rar压缩包解压
    elif rarfile.is_rarfile(zip_name):
        with rarfile.RarFile(zip_name, "r") as rar_ref:
            rar_ref.extractall(unpack_path)
    # else:
    #     logger.error(f"❌ Unable to parse this type of compressed file.") # 无法解析这类压缩包，错误日志
    #     return
    # 对解压之后的目录进行遍历
    for root,dirs,files in os.walk(unpack_path):
        for file in files:
            next_zip_name=os.path.join(root,file)
            # 判断二级文件是不是压缩包
            if zipfile.is_zipfile(next_zip_name) or tarfile.is_tarfile(next_zip_name) or rarfile.is_rarfile(next_zip_name):
                next_unpack_path=os.path.splitext(next_zip_name)[0]
                recursive_unzip(next_zip_name,next_unpack_path)
    # 解压成功日志
    logger.info(f"✅ unpack successful!")

# 下载
def download_data(url:str,name:str=None,data_path:str=None,need_unpack:bool=True):
    r"""
    Download the file from the given file path to the specified path and unzip it.
    It is recommended to set the name.
    :param url: download url
    :param name: zip name (包含后缀.zip)
    :param data_path: zip root dir(压缩包根路径)
    :param need_unpack: Is it necessary to extract?(是否需要解压)
    :return: None
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
    # 获取文件类型
    file_type=str(response.headers.get("Content-Type"))
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
        "rar",
        "tar.gz",
        "gz"
    ]
    # 解压数据
    if need_unpack: # 判断是否需要解压压缩包
        try:
            # compress_type=name.split(sep=".")[1] # 获取压缩类型
            zip_name=name.split(sep=".")[0] # 获取要解压到文件的名称
            unpack_path=os.path.join(data_dir,zip_name) # 解压到文件的路径
            recursive_unzip(zip_path, unpack_path)
            # if compress_type in compression_formats:
            #     recursive_unzip(zip_path,unpack_path)
            # else:
            #     raise ValueError
        except IndexError as e:
            logger.warning(f"Not find compress file.")
        # except ValueError as e:
        #     logger.warning(f"Not find compress type.")

# Github加速组件
class GitHubAccelerator:
    def __init__(self):
        # 定义普通下载链接
        self.download_url=config.DOWNLOAD_URL
        # 定义raw下载链接
        self.raw_url=config.RAW_URL
        # 定义clone url下载链接
        self.clone_url=config.CLONE_URL
    # 重写github下载的url
    def rewrite_github_url(self,original_url:str,node_type:str="download")->List[Tuple[str,str,str]]:
        # 判断链接是否是github内部的链接
        accelerated_urls = []
        if "github.com" not in original_url:
            raise ValueError(f"{original_url} not is a github url!")
        #判断下载类型
        nodes=self.download_url if node_type=="download" else self.raw_url
        # if node_type=="download":
        #     nodes=self.download_url
        # elif node_type=="raw":
        #     nodes=self.raw_url
        # elif node_type=="clone":
        #     nodes=self.clone_url
        # else:
        #     nodes=self.download_url # 默认等于download_url
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
                    accelerated_url=original_url.replace(
                        "https://github.com",
                        node_url
                    ).replace("/blob/","/")
                    # accelerated_url=urljoin(node_url,original_url)
                else:
                    accelerated_url=original_url.replace(
                        "https://github.com",
                        node_url
                    )
            else:
                accelerated_url=original_url
            accelerated_urls.append((accelerated_url,countries,description))
        return accelerated_urls
    # 重写clone url:
    def rewrite_clone_url(self,original_url:str)->List[Tuple[str,str,str]]:
        stype=os.path.splitext(original_url)[1]
        accelerated_urls = []
        # 判断是否是clone url路径
        if stype!=".git":
            raise ValueError(f"{original_url} not is a clone url!")
        else:
            href_split = original_url.split("github.com", 1)[1]
            for node_url,countries,description in self.clone_url:
                if node_url.startswith("https://gitclone.com"):
                    accelerated_url=node_url+"/github.co"+href_split
                else:
                    accelerated_url=node_url+href_split
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
    def download_file(self,url_desc,name:str=None,data_path:str=None,need_unpack:bool=True):
        accelerated_url, countries, description= url_desc
        logger.info(f"📍 正在使用{countries}的节点。")
        logger.info(f"🙏 感谢{description}。")
        # 下载数据
        download_data(url=accelerated_url,name=name,data_path=data_path,need_unpack=need_unpack)
    # clone Project,运行之前请确认你已经安装了git
    def clone_project(self,accelerated_urls:List[Tuple[str,str,str]],target_directory:str=None):
        for accelerated_url, countries, description in accelerated_urls:
            if target_directory is None:
                target_directory=os.path.basename(accelerated_url).split(".")[0]
            logger.info(f"📍 正在使用{countries}的节点。")
            logger.info(f"🙏 感谢{description}。")
            try:
                # 判断是否指定clone到指定目录
                # if target_directory is None:
                #     subprocess.run(["git","clone",accelerated_url],timeout=300,check=True)
                # else:
                subprocess.run(["git", "clone", accelerated_url,target_directory], timeout=300, check=True)
                logger.info(f"✅ clone project successful!")
                break
            except subprocess.TimeoutExpired as e:
                # 删除项目文件，防止下一次clone时出错
                if os.path.exists(target_directory):
                    os.removedirs(target_directory)
                logger.error("⏰ time out!")
            except subprocess.CalledProcessError as e:
                # 删除项目文件，防止下一次clone时出错
                if os.path.exists(target_directory):
                    os.removedirs(target_directory)
                logger.error(f"❌ git 命令失败:{e}")
# 添加指令操作
def main():
    parser=argparse.ArgumentParser(description="🙂 Github accelerate tool")
    parser.add_argument("--clone",dest="clone",action="store_true") # 设置是否是clone url
    parser.add_argument("-u","--url",type=str,help="clone url/download url/raw url",dest="url") # 设置 url
    parser.add_argument("-t","--type",type=str,dest="type",choices=["download","raw"],default="download",help="download type") # 下载类型
    parser.add_argument("--zip_name","-z",type=str,dest="zip_name",help="zip name(Including the suffix)") # 设置压缩名称
    parser.add_argument("--data_path","-dp",dest="data_path",help="The path to save the compressed file") # 设置压缩包存放的路径
    parser.add_argument("--unzip",dest="unzip",action="store_true",help="Determine whether to extract") # 判断是否要解压
    args=parser.parse_args()
    # 编写逻辑
    # original_url="https://github.com/PowerShell/PowerShell.git"
    gitHub_accelerator = GitHubAccelerator()
    if args.clone:
        logger.info(f"📦 clone {args.url}") # 提示要克隆的项目
        urls = gitHub_accelerator.rewrite_clone_url(args.url)
        gitHub_accelerator.clone_project(accelerated_urls=urls)
    else:
        urls = gitHub_accelerator.rewrite_github_url(original_url=args.url,node_type=args.type)
        url_desc = gitHub_accelerator.get_fastest_node(urls)
        gitHub_accelerator.download_file(url_desc,name=args.zip_name,data_path=args.data_path,need_unpack=args.unzip)
if __name__=="__main__":
    main()