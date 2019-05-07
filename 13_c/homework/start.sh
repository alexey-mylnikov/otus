#!/bin/sh
set -xe

yum install -y epel-release
yum install -y  gcc \
				make \
				protobuf \
				protobuf-c \
				protobuf-c-compiler \
				protobuf-c-devel \
				python-pip \
				python-devel \
				python-setuptools \
				zlib-devel \
				gdb

ulimit -c unlimited
cd /tmp/otus/
protoc-c --c_out=. deviceapps.proto
python setup.py test
