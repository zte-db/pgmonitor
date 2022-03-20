# Postgresql监控工具pgmonitor

## 环境配置

推荐使用Python3。已测试在Python 2.7下也可运行。

用pip安装psycopg2。罕见情况下会报错library有问题，可尝试在~/.bashrc中添加以下内容：

```sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/
```

## 使用

默认不带参数运行pgmonitor.py即可。

```sh
python pgmonitor.py
```

打印信息：如果发生异常，会打印相关信息。默认不打印采集到的数据，若要打印则用--printall开启。

生成文件：采集的数据，每生成一行就刷新一次。第一行是表头，之后每一行是监控数据，用无空格逗号分隔。其中，第一列固定为python时间time.time()，之后每一列格式为大标题+短横线+小标题。默认文件名metrics.csv。

命令行参数如下：

--interval：数据采集间隔时间，单位秒，默认5

--omit：省略的采集项，默认time（即postgresql time，因为已经有python时间）

--host：pg服务器IP，默认localhost

--port：pg服务器端口，默认5432

--user：pg用户名，默认postgres

--pwd：pg用户的密码，默认postgres

--chances：每次采集的最大重连次数，默认2（旧版本默认4）

--printall：开关，若打开，打印采集到的数据。不写就不打印

--check：开关，若打开，则当第一条数据无法正常采集时退出程序，用于初次使用时测试数据库连接和插件安装是否正常。

--output：输出文件名，默认metrics.csv

注意：第一个时间戳的数据不会被记录，因为它无法计算一些增量指标。每个查询的时间限制为 interval*0.8/(chances+1) ，超时查询会立刻停止，并重新连接数据库，最大重连次数为chances（初次连接不计入）。所以chances越大，时间限制越短，可根据实际情况调节。

## 添加新采集项（未测试）

建议先编写dool插件，测试能够正常运行，再添加到queries.py

首先，仿照现有采集函数，编写要增加的采集函数。一种情况只有参数c（cursor），此类函数不能记录前一次采集的数据。另一种情况有参数(c, prev, elapsed)，此类函数可以记录前一次采集的数据，从而计算这段时间内的增量，建议将增量除以elapsed（时间）来使用。其中，prev和return的curr格式要一致，和return的val（采集结果list）不需要一致。

其次，按queries.py内的说明，修改其他函数，添加新采集项的信息。

最后运行测试。如需debug，可注释掉部分except。

## 其他文件

dool_pytime.py：dool插件，用python的time.time()采集时间数据

check_all.py：根据csv，检查数据缺失情况（第一条数据不算），依次打印缺失个数、总采集项数、缺失比例、连续缺失2条及以上的数据段的个数、平均每个缺失段的连续缺失个数、最大连续缺失个数。输入文件名为metrics.csv。

check_result.py：根据pgmonitor打印信息，打印缺失个数。理论上和check_all.py打印的信息一致。输入文件名为result.txt。

## 推荐用法

因为dbsize, transactions, buffer容易缺数据，所以建议将它们和其他项分开采集，即：

```sh
python -u pgmonitor --omit time,dbsize,transactions,buffer > result1.txt
python -u pgmonitor --omit time,conn,lockwaits,settings > result2.txt
```

若在ubuntu的docker内使用pgmonitor，并不需要修改IP和端口，用默认的localhost和5432即可。

检查是否正确采集的方法：观察dbsize的后几个采集项，它们显示增量信息。若没有oltpbench运行，则数值为0；否则有数值。