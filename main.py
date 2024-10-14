# -*- encoding: utf-8 -*-
# File: main.py
# Description: None
import logging
import os
import pathlib
import re
import shutil
import subprocess
from typing import List, Optional

import click
import docker
import docker.errors
import pymupdf
from markdown_it import MarkdownIt
from tqdm import tqdm

from config import (
    BASE_PATH,
    DOCKER_MODE,
    EXTRACTED_FILE_PATH,
    LOCAL_MODE,
    ORIGIN_FILE_PATH,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def run_command(command: str):
    result = subprocess.run(command, text=True, shell=True)
    if result.returncode != 0:
        raise subprocess.SubprocessError(f"commnad error, check please:{command}")


def get_mode_command(mode: str, pdf_path: str):
    path_name = os.path.split(pdf_path)[-1]
    if mode is DOCKER_MODE:
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


def handle_table_for_md(tokens):
    # 处理表格异常
    handle_tokens, length, index = [], len(tokens), 0
    while length > index:
        token = tokens[index]
        if "</table>" in token:
            table_tokens, final_list = [], []
            for _index in range(index, length):
                _token = tokens[_index]
                if "</table>" in _token:
                    table_tokens.append(re.sub(r"^<td>|</td>$", "", _token.strip()))
                else:
                    index = _index
                    break
            table_tokens_length = len(table_tokens)
            if table_tokens_length == 2:
                for _idx, _tk in enumerate(table_tokens):
                    if _idx == 0:
                        _tk = re.sub(r"</table>$", "", _tk)
                    else:
                        _tk = re.sub(r"^<table[^>]*>", "", _tk)
                    final_list.append(_tk)
            elif table_tokens_length > 2:
                for _idx, _tk in enumerate(table_tokens):
                    if _idx == 0:
                        _tk = re.sub(r"</table>$", "", _tk)
                    elif _idx == table_tokens_length - 1:
                        _tk = re.sub(r"^<table[^>]*>", "", _tk)
                    else:
                        _tk = re.sub(r"^<table[^>]*>|</table>$", "", _tk)
                    final_list.append(_tk)
            else:
                final_list = table_tokens

            token = "".join(final_list)
        index += 1

        handle_tokens.append(token)
    return handle_tokens


def handle_header_for_md(tokens, toc: Optional[List] = None):
    if not toc:
        return tokens
    toc_index, toc_length = 0, len(toc) - 1
    handle_tokens = []
    for token in tokens:
        _token = token.strip("#").strip()
        if toc_index < toc_length:
            header_level, header_content, _ = toc[toc_index]
            if header_content == _token:
                _token = f"{'#'*header_level} {_token}"
                toc_index += 1
        handle_tokens.append(_token)
    return handle_tokens


def handle_md(md_file, toc):
    with open(md_file, "r") as f:
        _file = f.read()

    tokens = _file.split("\n\n")
    tokens = handle_table_for_md(tokens)
    tokens = handle_header_for_md(tokens, toc)
    return "\n\n".join(tokens)


def single_wrangler(origin_doc, handler_file, doc_name, auto_transfer):
    # choose mineru's file
    handler_type_folder = os.listdir(handler_file)[0]
    current_handler_file = os.path.join(
        handler_file, handler_type_folder, f"{doc_name}.md"
    )
    doc = pymupdf.open(origin_doc)
    toc = doc.get_toc()
    content = handle_md(current_handler_file, toc)
    file_name = f"{doc_name}.md"
    if auto_transfer:
        marker = MarkdownIt()
        content, file_name = marker.render(content), f"{doc_name}.html"
    return content, file_name


def wrangler(extractor_path: str, output_path: str, auto_transfer: bool):
    documents = [extractor_path]
    if os.path.isdir(extractor_path):
        documents = [
            file_name.split(".")[0]
            for file_name in os.listdir(extractor_path)
            if os.path.isfile(os.path.join(extractor_path, file_name))
        ]
    # 每个文件单独处理
    for origin_doc in tqdm(documents, desc="File processing..."):
        doc_name = pathlib.Path(origin_doc).name.split(".")[0]
        handler_file = os.path.join(EXTRACTED_FILE_PATH, doc_name)
        content, file_name = single_wrangler(
            origin_doc, handler_file, doc_name, auto_transfer
        )
        with open(os.path.join(output_path, file_name), "w") as f:
            f.write(content)


def extractor(extractor_path: str):
    mode, exist = check_commad_exist()
    if not exist:
        raise ModuleNotFoundError(
            "Missing PDF extractor moudle: MinerU, Please install it first"
        )
    command = get_mode_command(mode, extractor_path)
    run_command(command)


@click.command()
@click.option(
    "-p",
    "--file_path",
    prompt="files that need to be parsed, file or folder",
    required=True,
    type=str,
)
@click.option(
    "-o",
    "--output_folder",
    prompt="output_folder_path",
    required=True,
    type=str,
)
@click.option(
    "-a",
    "--auto_transfer",
    prompt="auto convert markdown to html",
    type=bool,
    default=False,
)
def main(file_path: str, output_folder: str, auto_transfer: bool):
    if not os.path.exists(BASE_PATH):
        for path in [BASE_PATH, EXTRACTED_FILE_PATH, ORIGIN_FILE_PATH]:
            os.mkdir(path)
    if not os.path.exists(output_folder) and os.path.isdir(output_folder):
        raise NotADirectoryError("directory not exist or the path is not a directory")
    # 进行文件转移
    run_command(f"cp -r {file_path} {ORIGIN_FILE_PATH}")
    path_name = os.path.split(file_path)[-1]
    extractor_path = os.path.join(ORIGIN_FILE_PATH, path_name)
    extractor(extractor_path)
    wrangler(extractor_path, output_folder, auto_transfer)


if __name__ == "__main__":
    main()
