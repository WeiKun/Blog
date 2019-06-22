# ssh&rsync搭建副机
开发时，不可避免出现需要多机部署测试的情况，如果每台机都是svn拉代码，未免不方便。

可以只用一台主开发机用于开发，其他机器用rsync执行代码/资源同步，ssh执行远程部署，达到一个让自己舒服的开发环境。

## ssh远程执行
只有用key登录的方式才能保证服务器之间安全地免密ssh登录/执行

如果想要远程执行某个命令，需要如下
```
ssh -P port user@xxx.xxx.xxx.xxx "ls -la"
```

命令好像只能是PATH里有的可执行文件，不能是.bashrc/.profile里alias的

如果执行的不止一两句，可以scp先发一个脚本文件过去，然后执行脚本文件，再删除

```
scp /path/filename username@servername:/path/
ssh -P port user@xxx.xxx.xxx.xxx "./filename"
ssh -P port user@xxx.xxx.xxx.xxx "rm filename"
```

这样就可以做到想在目标机器执行什么命令就执行什么命令的目的了

记得在所有服务器给user加上sudo免密，否则可能有些执行会有权限问题

## rsync
ssh/scp只能用来传小文件，传整个代码目录会非常麻烦的，所以这个时候需要用rsync了。

首先，肯定是在作为代码源的服务器（其实也可以在副机安装，然后主开发机推送）apt安装rsync。然后配置/etc/rsyncd.conf，例如

```
port=873                            #开放的port
log file=/var/log/rsync.log         #log文件
pid file=/var/run/rsyncd.pid        #pid文件
address=192.168.36.130              #指定哪个地址作为服务地址，如果单IP服务器，没必要

[test]                              #设定开放的模块名
path=/tmp/rsync                     #模块位置
use chroot=true                     #是否限定在该目录下，默认为true，当有软连接时，需要改为fasle,如果为true就限定为模块默认目录    
max connections=4                       # 指定最大可以连接的客户端数
read only=no                            #是否只读
list=true                               #是否可以列出模块名，用于查询，例如rsync 192.168.36.130::就能查询出来
uid=weikun                              #以哪个用户的身份来传输  
gid=weikun                              #以哪个组的身份来传输 
auth users=test                         #指定验证用户名，可以不设置
secrets file=/etc/rsyncd.passwd         #密码文件，可以不设置
hosts allow=192.168.36.131 （多个ip以空格隔开，也可以写ip段：192.168.36.0/24）  #允许访问的主机

```

然后在目标服使用rsync指令拉/推文件就好了，格式如下
```
rsync -xxx src tgt
```
例如

```
#推
rsync -av test1/ test@xxx.xxx.xxx.xxx::test/

#拉
rsync -av test@xxx.xxx.xxx.xxx::test/ test1/
```

具体每一个参数的含义如下

```
-a 包含-rtplgoD
-r 同步目录时要加上，类似cp时的-r选项
-v 同步时显示一些信息，让我们知道同步的过程
-l 保留软连接
-L 加上该选项后，同步软链接时会把源文件给同步
-p 保持文件的权限属性
-o 保持文件的属主
-g 保持文件的属组
-D 保持设备文件信息
-t 保持文件的时间属性
--delete 删除DEST中SRC没有的文件
--exclude 过滤指定文件，如--exclude "logs"会把文件名包含logs的文件或者目录过滤掉，不同步
-P 显示同步过程，比如速率，比-v更加详细
-u 加上该选项后，如果DEST中的文件比SRC新，则不同步
-z 传输时压缩
```

一般最好把-a、-v、--delete、-t、-o、-p、-u、-z加上

## 如何搭配
1. 先把.profile跟.bashrc（有时候还要.vimrc）同步到目标机，使用scp，这个两个文件既可以是专门为副机配置的，也可以是开发机自己的，这样如果有时候对这部分进行修改时，重复这一步就好了
2. 用一个rsync模块把工具脚本组织起来，然后同步过去，方便后续的部署启动
3. 用模块将需要部署的模块跟代码组织起来，同步过去（这部分也可以写在3的工具脚本中）
4. 最后用3里的工具脚本启动

这样除了看log，基本上没有特殊事情，就不需要在副机进行操作了