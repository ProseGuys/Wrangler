# Wrangler

> 当前服务所采用的PDF解析能力都基于MinerU, 在使用本服务之前, 需要在本地安装[MinerU服务](https://github.com/opendatalab/MinerU/blob/master/README_zh-CN.md)

提供基于MinerU生成的Markdown文件进行二次数据处理，包含分页表格合并，根据PDF自带元信息标题对markdown标题进行重新分级等能力

## 用法

Usage: main.py [OPTIONS]

Options:
  -p, --file_path TEXT         [required]
  -o, --output_folder TEXT     [required]
  -a, --auto_transfer BOOLEAN
  --help                       Show this message and exit.

- -p: 需要进行pdf解析的文件或者文件夹
- -o: 导出输出文件的文件夹地址
- -a: 是否自动将markdown文件转成html文件
