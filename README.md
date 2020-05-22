# PyIUpd 增量更新效率工具
每次都要手动上传文件到服务器，改动文件较多还需要备份，所以就写了个小工具

# 使用方法
1. 修改conf.ini，与upload.exe同级
```ini
[default]
# 本地需要增量更新的文件
localFilePath = C:\Users\XXX\Desktop\webapp
# 提交到服务器的同目录路径，逗号分隔，可提交多个目录
remotePath = /app/webapps,
; /app2/webapps
# 服务器即将覆盖文件的备份
backPath = D:\uploadBack

# 服务器配置信息
hostname = 192.168.x.x
port     =  22
username = root
password = 123456
```
2. 双击运行upload.exe

# 说明
本脚本工具自动比对覆盖文件，对将覆盖文件进行备份。
