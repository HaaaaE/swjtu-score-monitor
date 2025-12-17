#!/bin/bash

# 如果任何命令失败，则立即退出
set -e

# 第1步：安装系统依赖，为 Pillow 的编译做准备 (这部分是正确的，保持不变)
echo "--- Installing system dependencies for Pillow ---"
yum install -y \
  libjpeg-turbo-devel zlib-devel libtiff-devel freetype-devel \
  lcms2-devel libwebp-devel tcl-devel tk-devel harfbuzz-devel \
  fribidi-devel libraqm-devel libimagequant-devel libxcb-devel

# # 第2步：将所有 Python 依赖包作为文件直接安装到 'api/' 目录下
# echo "--- System dependencies installed. Installing Python packages directly into the 'api' directory ---"

# # 关键改动：使用 --target api
# # 这会把 fastapi, Pillow 等所有库的文件下载并放置在 api/ 文件夹下
# # 这样它们就会和你的函数代码一起被打包和部署
# pip install . --target api

echo "--- Build script finished. ---"
