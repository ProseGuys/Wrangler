# -*- encoding: utf-8 -*-
# File: config.py
# Description: None
import os

LOCAL_MODE = "LOCAL_MODE"
DOCKER_MODE = "DOCKER_MODE"

EXEC_MODES = [LOCAL_MODE, DOCKER_MODE]

BASE_PATH = "/tmp/wrangler"
ORIGIN_FILE_PATH = os.path.join(BASE_PATH, "origin_files")
EXTRACTED_FILE_PATH = os.path.join(BASE_PATH, "extrated_files")
