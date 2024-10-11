# -*- encoding: utf-8 -*-
# File: main.py
# Description: None
import logging
import os
import shutil
import subprocess

import docker
import docker.errors

from config import (
    BASE_PATH,
    DOCKER_MODE,
    EXEC_MODES,
    EXTRACTED_FILE_PATH,
    LOCAL_MODE,
    ORIGIN_FILE_PATH,
)

logger = logging.getLogger(__name__)


def run_command(command: str, is_log: bool = False):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )
    if is_log:
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())  # 实时打印输出
    if process.returncode != 0:
        raise subprocess.SubprocessError(f"command error: {process.communicate()[-1]}")


def get_mode_command(mode: str, pdf_path: str):
    path_name = pdf_path.split()[-1]
    if mode is DOCKER_MODE:
        run_command(f"mv ")
        command = f"docker run -v {BASE_PATH}:/volumn -v $(pwd)/magic-pdf.json:/root/magic-pdf.json --gpus=all mineru:latest /bin/bash -c 'magic-pdf -p /volumn/origin_files/{path_name} -o /volumn/extrated_files'"
    if mode is LOCAL_MODE:
        command = f"magic-pdf -p {pdf_path} -o {EXTRACTED_FILE_PATH}"
    return command


def check_commad_exist():
    if shutil.which("magic-pdf") is not None:
        return LOCAL_MODE, True
    client = docker.from_env()
    try:
        client.images.get("mineru:latest")
        return DOCKER_MODE, True
    except docker.errors.ImageNotFound:
        return None, False


def wrangler():
    pass


def extractor(pdf_path: str):
    mode, exist = check_commad_exist()
    if not exist:
        raise ModuleNotFoundError(
            "Missing PDF extractor moudle: MinerU, Please install it first"
        )
    command = get_mode_command(mode, pdf_path)
    # 执行转换脚本
    logger.info(command)
    run_command(command, is_log=True)


def main(pdf_path: str, output_path):
    # 进行文件转移
    run_command(f"cp -r {pdf_path} {ORIGIN_FILE_PATH}")
    pdf_name = os.path.split(pdf_path)[-1]
    pdf_path = os.path.join(ORIGIN_FILE_PATH, pdf_name)
    # 数据提取
    extractor(pdf_path)
    # 数据清洗
    wrangler(pdf_path)
    # 数据整理


if __name__ == "__main__":
    pass
