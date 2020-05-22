import os
# 命令库
import paramiko

# 打包命令  pyInstaller -F upload.py


# 从配置文件读取配置
import configparser
conf = configparser.ConfigParser()
conf.read("conf.ini", encoding='UTF-8')

# 待复制文件列表
localFilePath = conf.get("default", "localFilePath") or ""
# 服务器目录路径
remotePath = conf.get("default", "remotePath").split(",") or []
# 备份文件目录
backPath = conf.get("default", "backPath") or ""
# 服务器地址
ssh_conf = {
    "hostname": conf.get("default", "hostname") or "",
    "port": conf.get("default", "port") or "",
    "username":  conf.get("default", "username") or "",
    "password": conf.get("default", "password") or ""
}


# 过滤字符串
def normalize(path):
    if not path.endswith("/"):
        path += "/"
    path = path.replace("\\", "/")
    path = path.replace("\n", "")
    return path


localFilePath = normalize(localFilePath)
backPath = normalize(backPath)
remotePath = [normalize(path) for path in remotePath if(len(str(path)) != 0)]


# 获取ssh对象
def get_ssh():
    # 首先指定你的私钥在哪个位置（ssh是自动找到这个位置，Python不行，必须指定）
    # private_key = paramiko.RSAKey.from_private_key_file('id_rsa')

    # 创建SSH对象
    ssh = paramiko.SSHClient()
    # 允许连接不在know_hosts文件中的主机，否则可能报错：
    # paramiko.ssh_exception.SSHException: Server '192.168.43.140' not found in known_hosts
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 连接服务器
    try:
        ssh.connect(hostname=ssh_conf.get("hostname"),
                    port=ssh_conf.get("port"),
                    username=ssh_conf.get("username"),
                    password=ssh_conf.get("password"))
    except TimeoutError as e:
        print("连接远程服务器超时，请检查连接配置！")

    # stdin：标准输入（就是你输入的命令）；
    # stdout：标准输出（就是命令执行结果）；
    # stderr:标准错误（命令执行过程中如果出错了就把错误打到这里）
    # stdout和stderr仅会输出一个
    # stdin, stdout, stderr = ssh.exec_command('df')

    # 获取命令结果
    # 这个有问题，不显示错误，可以修改一下，先判断stdout有没有值，如果输出没有，就显示错误
    # result = stdout.read().decode()

    # 关闭连接
    # ssh.close()
    return ssh


# 获取当前的时间
def get_current_time(is_chinese=False):
    import time
    import locale
    if not is_chinese:
        return time.strftime('%Y-%m-%d %H:%M:%S')
    elif is_chinese:
        locale.setlocale(locale.LC_CTYPE, 'chinese')
        return time.strftime('%Y年%m月%d日%H时%M分%S秒')


# 打印配置信息
print("待上传文件目录(localFilePath)："+localFilePath)
print("远程服务器目录(remotePath)：")
for path in remotePath:
    print(path)
print("配置文件保存目录(backPath)："+backPath)
print("服务器连接信息：")
for key, value in ssh_conf.items():
    print('{key}:{value}'.format(key=key, value=value))
os.system('pause')

# 获取ssh连接对象
print("---正在连接远程服务器---")
ssh = get_ssh()
print("---远程服务器连接成功---")
sftp = ssh.open_sftp()
succ_count = 0
error_count = 0

# 待上传文件
wait_upload_file_list = []
for path, dir_list, file_list in os.walk(localFilePath):
    # 同步的路径
    afterPath = path.replace(localFilePath, "")
    # 反斜转正斜
    afterPath = afterPath.replace("\\", "/")

    # 待复制的文件
    for file in file_list:
        filePath = afterPath + "/" + file
        wait_upload_file_list.append((localFilePath+filePath, filePath))

# 先做备份
print("---开始备份服务器文件---")
backPath += get_current_time(True) + "/"
# 目录备份
for path in remotePath:

    for item in wait_upload_file_list:

        localPath = item[0]
        filePath = item[1]

        backLocalPath = backPath + path.replace("/", "#") + "/" + filePath
        # 创建目录
        try:
            if not os.path.exists(os.path.dirname(backLocalPath)):
                os.makedirs(os.path.dirname(backLocalPath))
        except PermissionError as e:
            print("创建备份目录失败：权限不足")
            print("---停止运行---")
            exit(0)

        try:
            # path均为带文件后缀，不能是目录，且不能是反斜杠路径
            sftp.get(path + filePath, backLocalPath)
        except FileNotFoundError as e:
            print("备份文件["+path + filePath+"]失败，文件不存在")
            pass
        except PermissionError as e:
            print("备份文件["+path + filePath+"]失败,权限不足")
            print("---停止运行---")
            exit(0)

print("备份完成，备份保存目录："+backPath)
os.system('pause')
print("---开始上传文件至服务器---")
# 上传文件
for path in remotePath:
    for item in wait_upload_file_list:
        localPath = item[0]
        filePath = item[1]
        try:
            # 创建远程目录
            remoteDir = os.path.dirname(path + filePath)
            ssh.exec_command("mkdir -p " + remoteDir)

            sftp.put(localPath, path + filePath)
            print("已上传文件["+localPath+"]至["+path + filePath+"]")
        except FileNotFoundError as e:
            print("失败")
            print(e)
            error_count += 1
            continue
        except PermissionError as e:
            error_count += 1
            print("上传文件["+localPath+"]失败,权限不足")
            continue
        except Exception as e:
            error_count += 1
            print("上传文件["+localPath+"]失败"+",错误：")
            print(e)
            continue
        succ_count += 1

print("上传完毕，成功" + succ_count.__str__() + "个,失败" + error_count.__str__() + "个")

# 关闭连接
ssh.close()

os.system('pause')
