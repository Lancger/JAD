#!/bin/bash
# Author: xuki.xu
# Dept: 系统运维部 
# Description: 本脚本实现Tomcat部署、移除和重启等功能;
# History:
# 2015-08-24 创建此脚本


#环境依赖：rsync/curl/awk/sed/wget/nc

#######################################################################
### 定义和初始化全局变量 

### Set PATH
PATH=/usr/local/bin:/usr/bin:/bin:/sbin:$PATH
export PATH

#定义程序BASE path
g_s_BASE_PATH=$(cd "$(dirname "$0")";cd ..; pwd)

### 定义rsync路径
g_fn_RSYNC="/usr/bin/rsync"
g_s_RSYNC_OPTIONS="-azKIr"

### 定义发布系统上传文件接口
g_s_TOMCAT_LOG_UPLOAD_URL="http://aud.inzwc.com/tomcatlogs/"

### 定义发布系统上传任务日志文件接口
g_s_TASK_LOG_UPLOAD_URL="http://aud.inzwc.com/tasklogs/"

### 定义日志写入路径
g_s_LOGDATE=`date +"%F"` 
g_s_LOGFILE="${g_s_BASE_PATH}/logs/tomcat.${g_s_LOGDATE}.log"

#定义任务更新状态提交接口
g_s_TASK_STATUS_API="http://aud.inzwc.com/api/v1.0/tomcat_task/modify_status/"

### Set script name variable
g_s_SCRIPT=`basename ${BASH_SOURCE[0]}`

g_s_TASK_FILE=""

### Initialize variables to default values
#任务编号
g_s_TASK_NO=""
#应用名
g_s_APP_NAME=""
#程序部署路径
g_s_APP_PATH=""
#Beta服务器IP地址
g_s_BETA_SERVER=""
#是否重启Tomcat
g_s_RESTART_TOMCAT=""
#Tomcat部署路径
g_s_TOMCAT_PATH=""
#Tomcat服务端口
g_s_TOMCAT_PORT=""
#是否重启Tomcat,默认不重启
g_s_RESTART_TOMCAT="0"
#rsync同步目录名称
g_s_RSYNC_PATH_NAME="opt"
#操作方式(0部署，1移除，2重启)
g_s_TYPE=""
#应用相对路径
g_s_APP_BASE_PATH=""
# 截取Tomcat启动日志存放位置 
g_s_TOMCAT_STARTUP_LOG=""
# 截取更新任务日志存放位置 
g_s_TASK_LOG=""
#Tomcat状态(数组,值为0表示正常,[0]代表进程,[1]代表curl请求返回是否200,[2]启动日志是否有WARN,[3]启动日志是否有ERROR,[4]启动日志是否有Exception)
g_a_TOMCAT_STATUS=(1 1 1 1 1)
#异常日志
g_s_ERROR_LOG=""

#延时执行时间,默认是0
g_s_DELAY_TIME=0

### Set fonts for help
g_s_NORM=`tput sgr0`
g_s_BOLD=`tput bold`
g_s_REV=`tput smso`

#######################################################################
### 参数和帮助 

### Help function
g_fn_HELP()
{
    echo -e \\n"${g_s_BOLD}发布系统Tomcat操作脚本${SCRIPT}${g_s_NORM}的帮助文档"\\n
    echo -e "${g_s_REV}用法:${g_s_NORM} ${g_s_BOLD}$g_s_SCRIPT 参数${g_s_NORM}"\\n
    echo "可选参数:"
    echo "${g_s_REV}-f${g_s_NORM}  --任务参数文件"
    echo -e "${g_s_REV}-h${g_s_NORM}  --显示此帮助并退出"\\n
    echo -e "示例: "
    #echo -e "${g_s_BOLD}整站更新：$g_s_SCRIPT -bUPA-aicai_webclient-20150721100208 -tb1946ac92492d2347c6235b4d2611184 -f0 -i192.168.91.40 -aaicai_webclient -w/data0/www/aicai/webclient/ -c/data0/opt/aicai/tomcat7_webclient/ -nwww -o10001 -x20001 -r1 ${g_s_NORM}"\\n
    exit 1
}

### Check the number of argument. If none are passed, print help and exit.
if [ $# -eq 0 ]; then
    g_fn_HELP 
fi

while getopts f: FLAG; do
    case $FLAG in
        f)
            g_s_TASK_FILE=$OPTARG
            ;;
        h) # show help
	    g_fn_HELP
            ;;
        \?) # unrecognized option - show help
            echo -e \\n"非法参数：-${g_s_BOLD}$OPTARG${g_s_NORM}"
	    g_fn_HELP
            ;;
    esac
done

shift $((OPTIND-1)) #  This tells getopts to move on to the next argument

#######################################################################
### 参数检查 

if [ -z $g_s_TASK_FILE ]; then
    echo "你必须指定${g_s_BOLD}更新参数文件${g_s_NORM}"
    exit -1
fi
    if [ -f $g_s_TASK_FILE ]; then
        source $g_s_TASK_FILE
    fi


if [ -z $g_s_TASK_NO ]; then
    echo "你必须指定${g_s_BOLD}更新任务号${g_s_NORM}"
    exit -1
fi
    echo "更新任务号：${g_s_BOLD}${g_s_TASK_NO}${g_s_NORM}"
    g_s_TASK_LOG=${g_s_BASE_PATH}/tasklogs/${g_s_TASK_NO}.log

if [ -z $g_s_APP_NAME ]; then
    echo "你必须指定${g_s_BOLD}更新应用名称${g_s_NORM}"
    exit -1
fi
    echo "更新应用名称：${g_s_BOLD}${g_s_APP_NAME}${g_s_NORM}"

if [ -z $g_s_APP_PATH ]; then
    echo "你必须指定${g_s_BOLD}更新应用路径${g_s_NORM}"
    exit -1
fi

if [ -z $g_s_TOMCAT_PATH ]; then
    echo "你必须指定${g_s_BOLD}Tomcat部署路径${g_s_NORM}"
    exit -1
fi
g_s_TOMCAT_STARTUP_LOG=${g_s_TOMCAT_PATH}/logs/${g_s_TASK_NO}.log

if [ -z $g_s_TYPE ]; then
    echo "你必须指定${g_s_BOLD}操作方式${g_s_NORM}"
    exit -1
#部署Tomcat
elif [ $g_s_TYPE = "0" ]; then
    echo "操作方式：${g_s_BOLD}部署Tomcat${g_s_NORM}"
#移除Tomcat
elif [ $g_s_TYPE = "1" ]; then
    echo "操作方式：${g_s_BOLD}移除Tomcat${g_s_NORM}"
#重启Tomcat
elif [ $g_s_TYPE = "3" ]; then
    echo "操作方式：${g_s_BOLD}重启Tomcat${g_s_NORM}"
fi

if [ -z $g_s_BETA_SERVER ]; then
    echo "你必须指定${g_s_BOLD}Beta服务器地址${g_s_NORM}"
    exit -1
fi
    echo "Beta服务器地址：${g_s_BOLD}${g_s_BETA_SERVER}${g_s_NORM}"

if [ -z $g_s_RSYNC_PATH_NAME ]; then
    echo "你必须指定${g_s_BOLD}rsync目录名称${g_s_NORM}"
    exit -1
fi
    echo "rsync目录名称：${g_s_BOLD}${g_s_RSYNC_PATH_NAME}${g_s_NORM}"


#######################################################################
### 函数定义 

### 日志写入文件  
g_fn_LOG()
{
	s_Ddate=`date +"%F %H:%M:%S"`
	echo "[$s_Ddate]"  "[$g_s_TASK_NO]"  "$*" >>$g_s_LOGFILE 
}


### 从Beta服务器同步需要的文件
g_fn_RsyncTomcatFileToLocal()
{
    g_fn_LOG "[Tomcat部署]从Rsync服务器获取Tomcat程序压缩包"
    g_fn_LOG "[Tomcat部署]开始进行文件同步操作:${g_s_BETA_SERVER}::${g_s_RSYNC_PATH_NAME}/${g_s_TOMCAT_PATH/\/data0\/opt/}.tar.gz 同步到 /tmp/"

    ${g_fn_RSYNC} ${g_s_RSYNC_OPTIONS} ${g_s_BETA_SERVER}::${g_s_RSYNC_PATH_NAME}/${g_s_TOMCAT_PATH/\/data0\/opt/}.tar.gz /tmp/ >/dev/null 2>&1 && g_fn_LOG "[文件同步]同步完成。" 
    g_fn_LOG "[Tomcat部署]创建Tomcat部署目录:${g_s_TOMCAT_PATH}"
    mkdir -p ${g_s_TOMCAT_PATH}
    g_fn_LOG "[Tomcat部署]压缩包:/tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz 解压到:${g_s_TOMCAT_PATH}"
    tar -xf /tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz -C ${g_s_TOMCAT_PATH}
    rm -f /tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz

    #检测下目录是否有文件
    t_s_FILE_COUNT=`find ${g_s_TOMCAT_PATH}|wc -l`
    g_fn_LOG "[Tomcat部署]Tomcat部署完成:${g_s_TOMCAT_PATH},文件数量：${t_s_FILE_COUNT}"
    if [ ${t_s_FILE_COUNT} -lt 10 ]; then
        return 3
    fi
        
    return 0
}

### Nginx过来的流量开关
g_fn_NginxTrafficSwitch()
{
    #nginx流量开启
    if [ $1 = "start" ]; then
        g_fn_LOG "[流量开关]Nginx流量开启: ${g_s_TOMCAT_PATH},端口: ${g_s_TOMCAT_PORT}"
    #nginx流量关闭
    elif [ $1 = "stop" ]; then
        g_fn_LOG "[流量开关]Nginx流量关闭: ${g_s_TOMCAT_PATH},端口: ${g_s_TOMCAT_PORT}"
    fi
}

### Tomcat重启脚本
g_fn_TomcatRestart()
{
    #停tomcat
    if [ $1 = "stop" ]; then
        #stop Tomcat
        g_fn_LOG "[Tomcat启停]停止Tomcat: ${g_s_TOMCAT_PATH}"
        ${g_s_TOMCAT_PATH}/bin/shutdown.sh >/dev/null 2>&1 
        sleep 5

        #等5秒，如果进程仍在，则强制杀掉
        t_s_TOMCAT_PID=`ps aux|grep java|grep ${g_s_TOMCAT_PATH}|awk '{print $2}'`
        if [ -z $t_s_TOMCAT_PID ]; then
            g_fn_LOG "[Tomcat启停]停止Tomcat成功: ${g_s_TOMCAT_PATH}"
        else
            kill -9 ${t_s_TOMCAT_PID} >/dev/null 2>&1
            g_fn_LOG "[Tomcat启停]停止Tomcat成功: ${g_s_TOMCAT_PATH}"

        fi

        #stop成功后删除work目录下文件
        g_fn_LOG "[Tomcat启停]删除work目录下文件: ${g_s_TOMCAT_PATH}"
        rm -rf ${g_s_TOMCAT_PATH}/work/* >/dev/null 2>&1

        return 0

    #启动tomcat
    elif [ $1 = "start" ]; then
        g_fn_LOG "[Tomcat启停]启动Tomcat: ${g_s_TOMCAT_PATH}"
        ${g_s_TOMCAT_PATH}/bin/startup.sh >/dev/null 2>&1 
        g_fn_LOG "[Tomcat启停]启动Tomcat操作完成: ${g_s_TOMCAT_PATH}"
    fi

}

### 截取更新任务日志
g_fn_TaskLogCut()
{
    g_fn_LOG "[任务日志]开始截取任务日志: ${g_s_TASK_LOG}"
    touch $g_s_TASK_LOG >/dev/null 2>&1
    if [ -f $g_s_TASK_LOG ]; then
        grep ${g_s_TASK_NO} ${g_s_LOGFILE} > ${g_s_TASK_LOG}
        g_fn_LOG "[任务日志]任务日志截取完成,日志行数：`wc -l ${g_s_TASK_LOG}`"
        
        #提交任务日志到更新服务器
        g_fn_PostTaskLogToAUD
    fi

}

### 截取Tomcat重启后日志
#建议是重启tomcat后至少1分钟再去获取日志，待Tomcat启动完成
g_fn_TomcatLogCut()
{
    g_fn_LOG "[Tomcat日志]开始截取Tomcat启动日志: ${g_s_TOMCAT_PATH}"
    t_s_DATE=`date +%Y-%m-%d`
    touch $g_s_TOMCAT_STARTUP_LOG >/dev/null 2>&1
    if [ -f $g_s_TOMCAT_STARTUP_LOG ]; then
        #获取tomcat最后一次启动时的日志位置
        t_s_TOMCAT_LAST_STARTUP_POSITION=`grep -n "org.apache.coyote.AbstractProtocol init" ${g_s_TOMCAT_PATH}/logs/catalina.${t_s_DATE}.out|tail -1|awk -F\: '{print $1}'`
        #从该位置到文件最后截取日志到g_s_TOMCAT_STARTUP_LOG
        sed -n "${t_s_TOMCAT_LAST_STARTUP_POSITION},$"p ${g_s_TOMCAT_PATH}/logs/catalina.${t_s_DATE}.out > $g_s_TOMCAT_STARTUP_LOG
        g_fn_LOG "[Tomcat日志]截取Tomcat启动日志,日志行数：`wc -l ${g_s_TOMCAT_STARTUP_LOG}`"

        #提交Tomcat启动日志到更新服务器
        g_fn_PostTomcatStartLogToAUD

    else
        g_fn_LOG "[Tomcat日志]截取Tomcat启动日志失败，请检查权限！"
    fi
}

### Tomcat重启异常判断
g_fn_TomcatStartIfOK()
{
    g_fn_LOG "[Tomcat启动检查]开始状态检查: ${g_s_TOMCAT_PATH}"

    #获取Tomcat运行进程PID
    t_s_TOMCAT_PID=`ps aux|grep java|grep tomcat|grep tmpdir=${g_s_TOMCAT_PATH}|awk '{print $2}'`
    #如果Tomcat PID进程存在
    if [ $t_s_TOMCAT_PID ]; then 
        #将tomcat状态数组赋值，为0表示进程正常运行中
        g_a_TOMCAT_STATUS[0]=0
        g_fn_LOG "[Tomcat启动检查]进程运行中: ${g_s_TOMCAT_PATH},进程PID：${t_s_TOMCAT_PID}"

        #最大请求3次
        t_s_MAX=3
        t_s_MIN=1

        #tomcat返回状态
        t_s_TOMCAT_SERVICE_CODE=0

        #判断Tomcat服务端口是否存在
        #最多重试3次，每次请求间隔10秒
        while [ $t_s_MIN -le $t_s_MAX ]
        do
            t_s_MIN=`expr $t_s_MIN + 1`

            nc -w10 -z 127.0.0.1 ${g_s_TOMCAT_PORT} >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                g_a_TOMCAT_STATUS[1]=0
                g_fn_LOG "[Tomcat启动检查]端口请求成功: ${g_s_TOMCAT_PATH},端口：${g_s_TOMCAT_PORT}"
                t_s_MIN=4
            else
                g_fn_LOG "[Tomcat启动检查]端口请求失败: ${g_s_TOMCAT_PATH},端口：${g_s_TOMCAT_PORT},请求次数：${$t_s_MIN}"
                sleep 10

            fi

        done
    else
        g_fn_LOG "[Tomcat启动检查]进程没有运行: ${g_s_TOMCAT_PATH}"
        if [ $g_s_ERROR_LOG ]; then
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"|Tomcat进程没有运行"
        else
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"进程没有运行"
        fi
    fi

    #检查日志
    t_s_WARN_COUNT=`grep -c "WARN" ${g_s_TOMCAT_STARTUP_LOG}`
    t_s_ERROR_COUNT=`grep -c "ERROR" ${g_s_TOMCAT_STARTUP_LOG}`
    t_s_EXCEPTION_COUNT=`grep -c "Exception" ${g_s_TOMCAT_STARTUP_LOG}`
    g_fn_LOG "[Tomcat启动检查]启动日志开始检查: ${g_s_TOMCAT_STARTUP_LOG}"
    if [ $t_s_WARN_COUNT -lt 1 ]; then
        g_a_TOMCAT_STATUS[2]=0
        g_fn_LOG "[Tomcat启动检查]启动未发现有WARN日志"
    else
        g_fn_LOG "[Tomcat启动检查]启动共有${t_s_WARN_COUNT}条WARN日志"
        if [ $g_s_ERROR_LOG ]; then
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"|[Tomcat启动检查]启动共有${t_s_WARN_COUNT}条WARN日志"
        else
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"[Tomcat启动检查]启动共有${t_s_WARN_COUNT}条WARN日志"
        fi
    fi
    
    if [ $t_s_ERROR_COUNT -lt 1 ]; then
        g_a_TOMCAT_STATUS[3]=0
        g_fn_LOG "[Tomcat启动检查]启动未发现有ERROR日志"
    else
        g_fn_LOG "[Tomcat启动检查]启动共有${t_s_ERROR_COUNT}条ERROR日志"
        if [ $g_s_ERROR_LOG ]; then
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"|[Tomcat启动检查]启动共有${t_s_ERROR_COUNT}条ERROR日志"
        else
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"[Tomcat启动检查]启动共有${t_s_ERROR_COUNT}条ERROR日志"
        fi
    fi
    
    if [ $t_s_EXCEPTION_COUNT -lt 1 ]; then
        g_a_TOMCAT_STATUS[4]=0
        g_fn_LOG "[Tomcat启动检查]启动未发现有Exception日志"
    else
        g_fn_LOG "[Tomcat启动检查]启动共有${t_s_EXCEPTION_COUNT}条Exception日志"
        if [ $g_s_ERROR_LOG ]; then
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"|[Tomcat启动检查]启动共有${t_s_EXCEPTION_COUNT}条Exception日志"
        else
            g_s_ERROR_LOG=${g_s_ERROR_LOG}"[Tomcat启动检查]启动共有${t_s_EXCEPTION_COUNT}条Exception日志"
        fi
    fi

    g_fn_LOG "[Tomcat启动检查]启动日志检查完成: ${g_s_TOMCAT_STARTUP_LOG}"
    
}


### 提交Tomcat日志到更新服务器接口
g_fn_PostTomcatStartLogToAUD()
{
    g_fn_LOG "[Tomcat日志上传]上传启动日志到自动发布系统服务器：${g_s_TOMCAT_STARTUP_LOG}" 
    curl -T ${g_s_TOMCAT_STARTUP_LOG} ${g_s_TOMCAT_LOG_UPLOAD_URL} >/dev/null 2>&1 && g_fn_LOG "[Tomcat日志上传]上传完成。"
}

### 提交更新日志到更新服务器接口
g_fn_PostTaskLogToAUD()
{
    g_fn_LOG "[任务日志上传]上传任务日志到自动发布系统服务器：${g_s_TASK_LOG}" 
    curl -T ${g_s_TASK_LOG} ${g_s_TASK_LOG_UPLOAD_URL} >/dev/null 2>&1 && g_fn_LOG "[任务日志上传]上传完成。"
}

### 调用发布系统接口，提交更新状态
g_fn_PostTomcatTaskStatusToAUD()
{
    #调用更新系统接口，提交更新状态
    g_fn_LOG "[任务状态接口调用]调用接口，返回更新结果..."
    t_s_TASK_STATUS=3
    #遍历tomcat状态检查结果，只要有状态为1(异常)，即将任务状态设置为2(更新完成，有异常),否则为3(更新完成，没有异常)
    for i in ${g_a_TOMCAT_STATUS[*]}
    do
        if [ $i -eq 1 ]; then
            t_s_TASK_STATUS=2
        fi

    done
    
    #操作状态
    if [ $1 ]; then
        t_s_DESC=$1
    fi
    
    #异常描述
    if [ $2 ]; then
        t_s_TASK_STATUS=$2
    fi

    t_s_CONCLUSION=`echo ${g_a_TOMCAT_STATUS[*]}|sed 's/ //g'`
    t_s_TASK_STATUS_DIC="{\"status\":${t_s_TASK_STATUS}, \"conclusion\":\"${t_s_CONCLUSION}\", \"desc\":\"${t_s_DESC}\"}"
    curl -i -H "Content-Type: application/json" -X POST -d "${t_s_TASK_STATUS_DIC}" ${g_s_TASK_STATUS_API}${g_s_TASK_NO} >/dev/null 2>&1 && g_fn_LOG "[任务状态接口调用]请求成功。"
}

#######################################################################
### 主程序执行

###更新前检测
### 检测本地是否能连通Beta(Rsync)服务器
nc -w10 -z ${g_s_BETA_SERVER} 873 >/dev/null 2>&1
if [ $? -ne 0 ]; then
    g_fn_LOG "[Tomcat操作前检查]异常：本机无法连通Beta(Rsync)服务器:${g_s_BETA_SERVER}"
    #调用发布系统接口告知更新失败原因
    g_fn_PostTomcatTaskStatusToAUD "[Tomcat操作前检查]异常：本机无法连通Beta(Rsync)服务器:${g_s_BETA_SERVER}" 2

    exit 1
fi

### 检测本机是否能连通发布系统服务器接口
nc -w10 -z aud.inzwc.com 80 >/dev/null 2>&1
if [ $? -ne 0 ]; then
    g_fn_LOG "[Tomcat操作前检查]异常：本机无法连通发布系统服务器."
    #调用发布系统接口告知更新失败原因
    g_fn_PostTomcatTaskStatusToAUD "[Tomcat操作前检查]异常：本机无法连通发布系统服务器." 2

    exit 1
fi

###部署Tomcat
if [ $g_s_TYPE -eq 0 ]; then
    g_fn_LOG "[Tomcat部署]开始操作:${g_s_TOMCAT_PATH}"
    if [ -d $g_s_TOMCAT_PATH ]; then
        g_fn_LOG "[Tomcat部署]异常：本机已存在Tomcat目录:${g_s_TOMCAT_PATH}"

        #关闭Tomcat
        g_fn_TomcatRestart stop

        #备份旧tomcat目录
        g_fn_LOG "[Tomcat部署]备份旧Tomcat目录:${g_s_TOMCAT_PATH} 到: ${g_s_TOMCAT_PATH}-${g_s_TASK_NO}"
        mv $g_s_TOMCAT_PATH ${g_s_TOMCAT_PATH}-${g_s_TASK_NO}
    fi


    #创建应用部署目录
    g_fn_LOG "[Tomcat部署]创建应用部署目录:${g_s_APP_PATH}"
    mkdir -p ${g_s_APP_PATH} 

    g_a_TOMCAT_STATUS=(0 0 0 0 0)

    #部署Tomcat
    g_fn_RsyncTomcatFileToLocal 
    if [ $? -eq 0 ] ; then
        # 调用发布系统接口，提交部署状态
        g_fn_PostTomcatTaskStatusToAUD "" 3
    else
        g_fn_LOG "[Tomcat部署]异常：Tomcat部署目录为空:${g_s_TOMCAT_PATH}"
        g_fn_PostTomcatTaskStatusToAUD "部署目录为空，请检查是否有准备Tomcat程序压缩包。" 2
    fi

    g_fn_LOG "[Tomcat部署]应用(${g_s_APP_NAME})Tomcat部署操作完成，任务号：${g_s_TASK_NO},Tomcat部署目录：${g_s_TOMCAT_PATH}"

###移除应用和Tomcat
elif [ $g_s_TYPE -eq 1 ]; then
    g_fn_LOG "[应用移除]开始操作:${g_s_APP_NAME}"
    #关闭Tomcat
    g_fn_TomcatRestart stop

    #删除应用部署目录
    g_fn_LOG "[应用移除]删除应用部署目录:${g_s_APP_NAME}"
    rm -rf ${g_s_APP_PATH}
    #删除Tomcat部署目录
    g_fn_LOG "[应用移除]删除Tomcat部署目录:${g_s_TOMCAT_PATH}"
    rm -rf ${g_s_TOMCAT_PATH}

    g_a_TOMCAT_STATUS=(0 0 0 0 0)

    # 调用发布系统接口，提交部署状态
    g_fn_PostTomcatTaskStatusToAUD "" 3

    g_fn_LOG "[应用移除]应用(${g_s_APP_NAME})和Tomcat移除操作完成，任务号：${g_s_TASK_NO}"



###重启Tomcat
elif [ $g_s_TYPE -eq 2 ]; then
    g_fn_LOG "[Tomcat重启]开始操作:${g_s_TOMCAT_PATH}"
    ### 检测本机是否有部署应用
    if [ ! -d $g_s_TOMCAT_PATH ]; then
        g_fn_LOG "[Tomcat重启]异常：本机未部署Tomcat:${g_s_TOMCAT_PATH}"
        #调用发布系统接口告知更新失败原因
        g_fn_PostTomcatTaskStatusToAUD "[Tomcat重启]异常：本机未部署Tomcat:${g_s_TOMCAT_PATH}" 2
    
        exit 1
    fi

    t_s_TOMCAT_PID=`ps aux|grep java|grep ${g_s_TOMCAT_PATH}|awk '{print $2}'`
    if [ $t_s_TOMCAT_PID ]; then
        #切走需要更新的Tomcat访问流量
        g_fn_NginxTrafficSwitch stop
    fi


    #关闭Tomcat
    g_fn_TomcatRestart stop

    #删除Tomcat bin目录下的cache文件
    g_fn_LOG "[Tomcat重启]删除Tomcat Bin目录下的Cache文件: ${g_s_TOMCAT_PATH}"
    rm -f ${g_s_TOMCAT_PATH}/bin/*cache* >/dev/null 2>&1
        
    #启动Tomcat
    g_fn_TomcatRestart start

    g_fn_LOG "[Tomcat重启]等待60秒，待Tomcat启动完成: ${g_s_TOMCAT_PATH}"
    sleep 60
    #截取Tomcat启动日志
    g_fn_TomcatLogCut
    
    #获取tomcat启动状态和日志报错情况，结果存入全局变量${g_a_TOMCAT_STATUS}
    g_fn_TomcatStartIfOK

    if [ $t_s_TOMCAT_PID ]; then
        #根据Tomcat启动情况，例如请求返回200，则切nginx访问流量过来
        if [ ${g_a_TOMCAT_STATUS[0]} -eq 0 ] && [ ${g_a_TOMCAT_STATUS[1]} -eq 0 ];then
            g_fn_NginxTrafficSwitch start
        fi
    fi

    # 调用发布系统接口，提交部署状态
    g_fn_PostTomcatTaskStatusToAUD ${g_s_ERROR_LOG}

    g_fn_LOG "[Tomcat重启]应用(${g_s_APP_NAME})Tomcat重启操作完成，任务号：${g_s_TASK_NO},Tomcat状态码：${g_a_TOMCAT_STATUS[*]}"

###Tomcat程序打包
elif [ $g_s_TYPE -eq 3 ]; then
    g_fn_LOG "[Tomcat程序打包]开始操作:${g_s_TOMCAT_PATH}"
    ### 检测本机是否有部署应用
    if [ ! -d $g_s_TOMCAT_PATH ]; then
        g_fn_LOG "[Tomcat程序打包]异常：本机未部署Tomcat:${g_s_TOMCAT_PATH}"
        #调用发布系统接口告知更新失败原因
        g_fn_PostTomcatTaskStatusToAUD "[Tomcat程序打包]异常：本机未部署Tomcat:${g_s_TOMCAT_PATH}" 2
    
        exit 1
    fi

    g_fn_LOG "[Tomcat程序打包]进入Tomcat部署目录:${g_s_TOMCAT_PATH}"
    cd ${g_s_TOMCAT_PATH}
    #去掉尾端的"/"
    g_s_TOMCAT_PATH=${g_s_TOMCAT_PATH%\/}
    tar -czf /tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz --exclude='work/*' --exclude='logs/*' ./ >/dev/null 2>&1 && g_fn_LOG "[Tomcat程序打包]Tomcat程序目录打包:${g_s_TOMCAT_PATH}，打包文件存储路径：/tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz"

    g_a_TOMCAT_STATUS=(0 0 0 0 0)

    if [ -f /tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz ]; then
        # 调用发布系统接口，提交部署状态
        g_fn_PostTomcatTaskStatusToAUD "打包文件:/tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz" 3 

        g_fn_LOG "[Tomcat程序打包]应用(${g_s_APP_NAME})Tomcat程序打包完成，任务号：${g_s_TASK_NO},打包文件存储路径：/tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz"
    else
        # 调用发布系统接口，提交部署状态
        g_fn_PostTomcatTaskStatusToAUD "打包文件/tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz不存在" 2 
        g_fn_LOG "[Tomcat程序打包]应用(${g_s_APP_NAME})Tomcat程序打包异常，任务号：${g_s_TASK_NO},打包文件不存在：/tmp/${g_s_TOMCAT_PATH##\/*\/}.tar.gz"
    fi

fi

# 截取更新日志到发布系统
g_fn_TaskLogCut

exit 0
