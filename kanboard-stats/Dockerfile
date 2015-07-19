#
# VERSION               0.0.2
FROM centos:7
MAINTAINER Fanday Dai "fandaydai@live.cn"

#reference:http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=4
RUN yum -y update
RUN yum -y install python-setuptools

RUN easy_install pip
RUN pip install influxdb
RUN pip install apscheduler
ADD files /files

ENV HOSTURL http://localhost:8000/jsonrpc.php
ENV AUTHKEY 095f206df206d1645fb19cf70bec7f601d2704b10b7d775c9d0f526a511b
ENV DATABASEHOST localhost
ENV DATABASEPORT 8086
ENV DATABASEUSER root
ENV DATABASEPWD root

CMD ["/bin/bash","-c","python /files/kanboard_stats.py"]

