#! -*- coding:utf-8 -*-
import os
import sys

file_path = os.path.abspath(__file__)
project_dir = os.path.split(os.path.split(file_path)[0])[0]
sys.path.insert(0, project_dir)
