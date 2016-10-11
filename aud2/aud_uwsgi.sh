#! /bin/bash
NAME=AUD
DESC="AUD uwsgi daemon"
d_start() {
    #/home/www/.virtualenvs/audenv/bin/uwsgi --ini /home/www/autodeploy/uwsgi.ini
    #/home/dev/demo/bin/uwsgi --ini /home/dev/project/ums/uwsgi.ini
    /home/www/.demo/bin/uwsgi --ini /home/www/aud2/uwsgi.ini
  }
d_stop() {
    #for pid in $(ps aux|grep /home/www/autodeploy/uwsgi.ini|awk '{print $2}')
    for pid in $(ps aux|grep /home/www/aud2/uwsgi.ini|awk '{print $2}')
    do
        kill -9 $pid >/dev/null 2>1&
    done
  }
 
case "$1" in
  start)
    echo -n "Starting $DESC: $NAME"
    d_start
    echo "."
    ;;
  stop)
    echo -n "Stopping $DESC: $NAME"
    d_stop
    echo "."
    ;;
  restart)
    echo -n "Restarting $DESC: $NAME"
    d_stop
    sleep 1
    d_start
    echo "."
    ;;
  *)
      echo "Usage: $SCRIPTNAME {start|stop|restart}" >&2
      exit 3
    ;;
esac
exit 0
