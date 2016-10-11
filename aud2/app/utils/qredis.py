#!/usr/bin/env python
# coding: utf-8
import redis
import json


class RedisTools:
    def qkeys(self, host, port, db):
        try:
            # Redis队列实例化
            data = []
            r = redis.StrictRedis(host=host, port=port, db=db)
            for queue in r.keys('*'):
                qlen = r.llen(queue)
                qdata = r.lrange(queue, start=0, end=-1)
                qdata_format = []
                for item in qdata:
                    try:
                        qdata_format.append(json.loads(item.replace('\\','')))
                    except:
                        qdata_format.append(item)
                # print type(qdata)
                data.append({'qlen': qlen, 'qdata': qdata_format, 'keys': queue})

            return data

        except Exception, exception:
            return [{}]
