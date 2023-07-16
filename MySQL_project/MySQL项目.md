# 基于keepalived+GTID的半同步主从复制MySQL集群

* __项目环境： __7台服务器（2G，2核），centos7，mysql.5.7.41，mysqlrouter8.0.21，keepalived2.0.10，ansilble

* __项目描述：__ 本项目的目的是构建一个高可用的、能实现读写分离的MySQL集群，确保业务的稳定，能批量部署和管理整个集群。

![MySQL项目图](MySQL项目.assets/MySQL项目图.jpg)

## 具体步骤：

### 准备工作

准备7台机器。

其中4台MySQL服务器，搭建主从复制的集群一个master服务器，2个slave服务器，一个延迟备份服务器。同时延迟备份服务器也可以充当异地备份服务器。

2台MySQLroute服务器，安装好keepalived软件，实现高可用的读写分离服务器。

一台ansible中控制服务器，实现对MySQL整个集群里的服务器进行批量管理。

#### 各服务器的IP地址：

master：192.168.232.147

slave1：192.168.232.141
slave2：192.168.232.148
slave3：192.168.232.149

ansible：192.168.232.144

router1：192.168.232.145
router2：192.168.232.146

### 一、配置master

#### 1、在master上安装配置半同步的插件

```
mysql>install plugin rpl_semi_sync_master soname 'semisync_master.so';
# 在master上设置超时时间为1秒
mysql>set global rpl_semi_sync_master_enabled = 1;
mysql>set global rpl_semi_sync_master_timeout = 1;
```

#### 2、修改配置文件

```
vim /etc/my.cnf
[mysqld]
innodb_buffer_pool_size = 1024M
character-set-server=utf8
# 开启二进制文件，设置id为1
log_bin
server_id = 1
# 设置超时时间为1秒
rpl_semi_sync_master_enabled=1
rpl_semi_sync_master_timeout=1000

```

修改配置文件之后要注意重启mysql服务

```
service mysqld restart
```

#### 3、在master上新建一个授权用户，给slave复制二进制日志

```
mysql>grant replication slave on *.* to 'chen'@'192.168.232.%' identified by 'Chen123#';
```

#### 4、导出master上的基础数据

```
mysqldump -uroot -p'Sanchuang123#' --all-databases --triggers --routines --events >all_db.SQL
# 将导出的数据传给ansible
scp all_db.SQL root@192.168.232.144:/root
```

### 二、配置slave

#### 1、在slave上安装配置半同步的插件

```
mysql>install plugin rpl_semi_sync_slave soname 'semisync_slave.so';
```

#### 2、修改slave的配置文件

设置半同步超时时间为1秒

```
mysql>set global rpl_semi_sync_slave_enabled=1;
```

```
vim /etc/my.cnf

[mysqld]
# 开启二进制日志，设置slave的id（不同机器的id不同）
log_bin
server_id = 2
# 在slave上设置半同步超时时间为1秒
rpl_semi_sync_slave_enabled=1
```

在master和slave上执行以下语句查看是否激活半同步

```
SELECT PLUGIN_NAME, PLUGIN_STATUS
FROM INFORMATION_SCHEMA.PLUGINS
WHERE PLUGIN_NAME LIKE '%semi%';

root@(none) 21:20  mysql>SELECT PLUGIN_NAME, PLUGIN_STATUS
    ->        FROM INFORMATION_SCHEMA.PLUGINS
    ->        WHERE PLUGIN_NAME LIKE '%semi%';
+----------------------+---------------+
| PLUGIN_NAME          | PLUGIN_STATUS |
+----------------------+---------------+
| rpl_semi_sync_master | ACTIVE        |
+----------------------+---------------+
1 row in set (0.03 sec)
```

#### 3、slave配置同步

```
mysql>stop slave;
mysql>reset slave all;
```

在slave上配置master info的信息

```
CHANGE MASTER TO MASTER_HOST='192.168.232.147',
 MASTER_USER='chen',
 MASTER_PASSWORD='Chen123#',
 MASTER_PORT=3306;
```

配置完成后开启服务，查看相关信息

```
mysql>start slave;
mysql>show slave status\G;
```

IO线程和SQL线程都已经开启，配置成功！

![image-20230712214940178](MySQL项目.assets/image-20230712214940178.png)

### 三、配置ansible

```
yum install epel-release -y
yum install ansible -y
```

#### 1、让ansible与所有的MySQL结点服务器建立免密通道

```
vim /etc/ansible/hosts
[db]
# 其他四台机器的IP
192.168.232.147
192.168.232.141
192.168.232.148
192.168.232.149
[dbslaves]
# 其他三台slave的IP
192.168.232.141
192.168.232.148
192.168.232.149
```

#### 2、生成RSA密钥对，并将公钥文件复制到目标主机上的对应文件中，以实现无密码登录

==复制公钥文件时需要其他服务都是开启的==

```
ssh-keygen -t rsa
ssh-copy-id -i /root/.ssh/id_rsa.pub root@（其他IP）
```

测试免密通道是否建立成功
``` 
ssh 'root@（其他IP）'
```

#### 3、拉取master的基础数据

```
scp root@192.168.232.147:/root/all_db.SQL .
```

#### 4、将拉取到的基础数据传到三台slave上

```
ansible -m copy -a "src=/root/all_db.SQL dest=/root" dbslaves
```

### 四、slave导入基础数据，完成基础数据同步

```
mysql -uroot -p'Sanchuang123#' <all_db.SQL
```

### 五、开启GTID功能

#### 1、在master配置文件/etc/my.cnf加上两行

```
[mysqld]
gtid-mode=ON
enforce-gtid-consistency=ON
```

#### 2、在slave配置文件/etc/my.cnf加上三行

```
[mysqld]
gtid-mode=ON
enforce-gtid-consistency=ON
# 自动更新
log_slave_updates=ON
```

#### 3、在slave配置master info的信息

```
mysql>reset master;
mysql>stop slave;
mysql>reset slave all;

mysql>CHANGE MASTER TO MASTER_HOST='192.168.232.147',
 MASTER_USER='chen',
 MASTER_PASSWORD='Chen123#',
 MASTER_PORT=3306,
 master_auto_position=1;
 
 mysql>start slave;
 mysql>show slave status\G;
```

最后显示IO进程和SQL进程都已经起来，并且GTID事务位置显示为1，GTID功能成功开启！

![image-20230713213454636](MySQL项目.assets/image-20230713213454636.png)

![image-20230713213127664](MySQL项目.assets/image-20230713213127664.png)

### 六、配置延迟备份服务器slave3，从slave1上拿二进制日志

#### 1、在slave1上安装配置半同步的插件

```
mysql>install plugin rpl_semi_sync_master soname 'semisync_master.so';
# 在master上设置超时时间为1秒
mysql>set global rpl_semi_sync_master_enabled = 1;
mysql>set global rpl_semi_sync_master_timeout = 1;
```

#### 2、修改slave1的配置文件

```
vim /etc/my.cnf
[mysqld]

# 设置超时时间为1秒
rpl_semi_sync_master_enabled=1
rpl_semi_sync_master_timeout=1000
```

slave1输入以下命令查看半同步是否激活成功

```
root@(none) 09:24  mysql>SELECT PLUGIN_NAME, PLUGIN_STATUS
    -> FROM INFORMATION_SCHEMA.PLUGINS
    -> WHERE PLUGIN_NAME LIKE '%semi%';
+----------------------+---------------+
| PLUGIN_NAME          | PLUGIN_STATUS |
+----------------------+---------------+
| rpl_semi_sync_master | ACTIVE        |
| rpl_semi_sync_slave  | ACTIVE        |
+----------------------+---------------+
2 rows in set (0.00 sec)

```

#### 3、在slave1上新建一个授权用户，给slave3复制二进制日志

```
mysql>grant replication slave on *.* to 'cheng'@'192.168.232.%' identified by 'Cheng123#';
```

#### 4、导出slave1上的基础数据

```
mysqldump -uroot -p'Sanchuang123#' --all-databases --triggers --routines --events >all_db.SQL
# 将导出的数据传给slave3
scp all_db.SQL root@192.168.232.149:/root
```

#### 5、slave3导入基础数据

```
mysql -uroot -p'Sanchuang123#' <all_db.SQL
```

#### 6、在slave3上清除master和slave的信息，并配置master info的信息

```
mysql>reset master;
mysql>stop slave;
mysql>reset slave all;

mysql>CHANGE MASTER TO
MASTER_HOST='192.168.232.141',
 MASTER_USER='cheng',
 MASTER_PASSWORD='Cheng123#',
 MASTER_PORT=3306,
 master_auto_position=1;
 
 mysql>start slave;
 mysql>show slave status\G;
```

出现以下信息就表示slave3到slave1的半同步配置成功

![image-20230714093244065](MySQL项目.assets/image-20230714093244065.png)

![image-20230714093259212](MySQL项目.assets/image-20230714093259212.png)

#### 7、在slave3上配置延迟备份

设置延迟备份时间为100秒

```
mysql>stop slave;
mysql>change master to master_delay = 100;
mysql>start slave;
mysql>show slave status\G;
```

看到以下值表示配置成功

![image-20230714094254968](MySQL项目.assets/image-20230714094254968.png)

### 七、创建计划任务每天进行master数据库的备份

#### 1、在master和ansible服务器之间建立双向免密通道，方便同步数据

```
ssh-keygen -t rsa
ssh-copy-id -i /root/.ssh/id_rsa.pub root@192.168.232.144
```

#### 2、编写备份脚本

```
cat /backup/backup_alldb.sh
#!/bin/bash

mkdir -p /backup
mysqldump -uroot -p'Sanchuang123#' --all-databases --triggers --routines --events >/backup/$(date +%Y%m%d%H%M%S)_all_db.SQL
scp /backup/$$(date +%Y%m%d%H%M%S)_all_db.SQL 192.168.232.144:/backup
```

#### 4、创建计划任务

每天4点执行备份脚本

```
crontab -e
0 4 * * * bash /backup/backup_alldb.sh
```

### 八、在另外的服务器上安装部署mysqlrouter中间件软件，实现读写分离

#### 1、在浏览器上下载rpm软件

https://dev.mysql.com/get/Downloads/MySQL-Router/mysql-router-community-8.0.23-1.el7.x86_64.rpm

#### 2、将下载好的软件传入，安装

```
rpm -ivh mysql-router-community-8.0.23-1.el7.x86_64.rpm
```

#### 3、修改配置文件

```
cd /etc/mysqlrouter/
vim mysqlrouter.conf

[logger]
level = INFO

# read-only
[routing:slaves]
# 设置地址为0.0.0.0，以便于后面的vip实现
bind_address = 0.0.0.0:7001
destinations = (slave1的IP):3306,(slave2的IP):3306
mode = read-only
connect_timeout = 1
# write and read
[routing:masters]
bind_address = 0.0.0.0:7002
destinations = (master的IP):3306
mode = read-write
connect_timeout = 2
```

修改配置文件之后启动MySQL router服务

```
service mysqlrouter restart
```

#### 4、查看监听端口

```
yum install net-tools -y
netstat -anplut|grep mysql

[root@router1 mysqlrouter]# netstat -anplut|grep mysql
tcp        0      0 192.168.232.145:7001    0.0.0.0:*               LISTEN      18384/mysqlrouter   
tcp        0      0 192.168.232.145:7002    0.0.0.0:*               LISTEN      18384/mysqlrouter 
```

#### 5、在master上创建2个测试账号，一个是写的，一个是读的

```
grant all on *.* to 'chen-w'@'%' identified by 'Chen123#';
grant select on *.* to 'chen-r'@'%' identified by 'Chen123#';
```

#### 6、在客户端上测试读写分离的效果，使用两个账号

==注意关闭所有的防火墙==

```
systemctl stop firewalld
systemctl disable firewalld
```

测试

```
mysql -h (router的IP) -P 7001 -uchen-r -p'Chen123#'
mysql -h (router的IP) -P 7002 -uchen-w -p'Chen123#'
```

查看连接的IP

```
show processlist;
```

### 九、安装keepalived实现高可用

#### 1、在两台mysql router上安装keepalived软件

```
yum install keepalived -y
```

#### 2、修改配置文件

```
cd /etc/keepalived/
vim keepalived.conf

# 把virtual_server内容全部删除
# vrrp_strict 		注释掉这行
```

修改router1中的配置文件

```
vrrp_instance VI_1 { # 定义一个vrrp协议实例VI_1
	state MASTER 		# 做master角色
	interface ens33 	#指定监听网络的接口，其实就是vip绑定到那个接口上 
	virtual_router_id 80 	# 虚拟路由器id
	priority 200 		# 优先级 0~255
	advert_int 1 		# 宣告消息的时间间隔1s
	authentication {
		auth_type PASS 	# 密码认证 password
		auth_pass 1111 	# 具体密码
	}
	virtual_ipaddress { 	# vip 虚拟ip地址
		192.168.232.188  	# ping一下看能不能用
	}
}
```

修改router2中的配置文件

```
vrrp_instance VI_1 {
	state backup 			# 做备用角色
	interface ens33
	virtual_router_id 80
	priority 100
	advert_int 1
	authentication {
		auth_type PASS
		auth_pass 1111
	}
	virtual_ipaddress {
		192.168.232.188
	}
}
```

配置完成后刷新服务

```
service keepalived start
```

可以看到router1有配置的192.168.232.188这个vip，而router2没有

![image-20230714184301317](MySQL项目.assets/image-20230714184301317.png)

![image-20230714184333407](MySQL项目.assets/image-20230714184333407.png)

### 十、配置2个vrrp实例实现双vip的高可用功能

在router1配置文件里创建第二个实例，与router2互为主从

```
vrrp_instance VI_2 {
    state backup
    interface ens33
    virtual_router_id 26
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    virtual_ipaddress {
        192.168.232.189
    }
}
```

在router2配置文件里创建第二个实例

```
vrrp_instance VI_2 {
    state MASTER
    interface ens33
    virtual_router_id 26
    priority 200
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    virtual_ipaddress {
        192.168.232.189
    }
}
```



