#! /bin/bash
# 检查更新文件是否存在，路径是否正确
# 

FILE_LIST_BASE_DIR="/data0/www/aud.inzwc.com/filelist/"
FILE_LIST=${FILE_LIST_BASE_DIR}${1}
RSYNC_TEST_OPTIONS="  -avzKIr -n  "
UPDATE_FILE_TEST_PATH="/tmp/update_test_path/"
RSYNC="/usr/bin/rsync"
RSYNC_USER=$2
RSYNC_BETA_SERVER=$3
RSYNC_PATH_NAME=$4
RSYNC_TEST_LOG="/tmp/filelist_rsync_test.log"

mkdir -p $UPDATE_FILE_TEST_PATH
cat /dev/null >$RSYNC_TEST_LOG
sed -e 's/\/data0\/www//;s/\/mfs\/ShareFile\/res//' -e "s/^[ \t]*//g" -e "s/[ \t]*$//g" $FILE_LIST >/tmp/filelist
$RSYNC $RSYNC_TEST_OPTIONS --files-from=/tmp/filelist ${RSYNC_USER}@${RSYNC_BETA_SERVER}::${RSYNC_PATH_NAME}/ $UPDATE_FILE_TEST_PATH --stats >$RSYNC_TEST_LOG  2>&1  
echo "$RSYNC $RSYNC_TEST_OPTIONS --files-from=/tmp/filelist ${RSYNC_USER}@${RSYNC_BETA_SERVER}::${RSYNC_PATH_NAME}/ $UPDATE_FILE_TEST_PATH --stats >$RSYNC_TEST_LOG  2>&1 " 
if [ $? -eq 0 ]; then
    echo "UpdateFileListCheckOK" >> $RSYNC_TEST_LOG
    echo "同步文件列表检查OK!" >> $RSYNC_TEST_LOG
fi
cat $RSYNC_TEST_LOG

