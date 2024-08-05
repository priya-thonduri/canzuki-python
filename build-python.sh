#!/bin/bash

# Works with Ubuntu 24.04
apt -y install gcc g++ make bzip2 patchelf pkg-config libssl-dev libffi-dev libbz2-dev lzma-dev liblzma-dev python3-dev

latest3=`curl -L https://www.python.org/ftp/python 2>/dev/null|\grep href|cut -d'>' -f2|cut -d'/' -f1|sort -n -t . -k 1,1 -k 2,2 -k 3,3|tail -3`
latest=`echo "$latest3"|head -1`
latestalpha=`echo "$latest3"|head -2|tail -1`
latestalpha2=`echo "$latest3"|tail -1`
for tryme in $latestalpha2 $latestalpha $latest; do
 wget https://www.python.org/ftp/python/$tryme/Python-$tryme.tar.xz
 if [ $? -eq 0 ]; then
  echo Python-$tryme.tar.xz exists.  Aborting.
  break
 fi
 tryme=""
done
echo "Latest versions: $latestalpha2 $latestalpha $latest"
[ x"$tryme" == x ] && ver=3.12.4 || ver=$tryme
echo "We will fetch $ver"

ver2=`echo "$ver"|tr -d .`
ver3=`echo "$ver"|cut -d. -f1,2`
ver4=`echo "$ver"|cut -d. -f1`
interpreter=`readelf -l /usr/bin/ls|\grep -m1 interpreter|tr -d '[]'|awk '{print $NF}'`
linkinterpreter=`stat -c%N $interpreter|awk '{print $3}'|tr -d "'"`
if [ `echo "$linkinterpreter"|grep -c "^/"` -eq 0 ]; then
 linkinterpreter=`dirname $interpreter`/$linkinterpreter
 lddir=`dirname $linkinterpreter`
else
 lddir=/lib/x86_64-linux-gnu/
fi
interpreterbase=`basename $linkinterpreter`
echo "Interpreter = $linkinterpreter"
echo "LD Dir = $lddir  Interpreter basefile=$interpreterbase"
nproc=`cat /proc/cpuinfo |grep ^processor -c`
echo "Number of processors=$nproc"
cd
if [ ! -e Python-$ver.tar.xz ]; then
 wget https://www.python.org/ftp/python/$ver/Python-$ver.tar.xz
fi
tar -xvf Python-$ver.tar.xz
[ $? -ne 0 ] && { echo "Problem. Aborting." ; exit ;}
cd ~/Python-$ver
./configure --prefix=/opt/canzuki/python/$ver --enable-shared
mkdir -p /opt/canzuki/python/$ver
make -j${nproc}
make install
cd /opt/canzuki/python/$ver/bin
ln -s pip$ver4 pip
ln -s python$ver4 python
export LD_LIBRARY_PATH=/opt/canzuki/python/$ver/lib
./pip list 
/opt/canzuki/python/$ver/bin/python$ver3 -m pip install --upgrade pip
./pip install requests
./pip install psutil 
patchelf --set-interpreter /opt/canzuki/python/$ver/lib/$interpreterbase --set-rpath /opt/canzuki/python/$ver/lib python$ver3
cd ../lib
cd /usr/lib/x86_64-linux-gnu/
cp libssl.so.[0-9] libcrypto.so.[0-9] libpthread.so.[0-9] libbz2.so.[0-9].[0-9] liblzma.so.[0-9] libexpat.so.[0-9] libm.so.[0-9]  libz.so.[0-9] libc.so.[0-9] $interpreterbase /opt/canzuki/python/$ver/lib
#cp ld-linux-x86-64.so.2 /opt/canzuki/python/$ver/lib/ld-linux.so.2
cd /
tar --exclude *__pycache__* -cjvf /tmp/python$ver2.tbz opt/canzuki/python/$ver

echo "Made /tmp/python$ver2.tbz"
ls -l /tmp/python$ver2.tbz 

echo "Testing python:"
LD_LIBRARY_PATH=/opt/canzuki/python/$ver/lib /opt/canzuki/python/$ver/bin/python -V
LD_LIBRARY_PATH=/opt/canzuki/python/$ver/lib /opt/canzuki/python/$ver/bin/pip list
LD_LIBRARY_PATH=/opt/canzuki/python/$ver/lib /opt/canzuki/python/$ver/bin/python << EOF
import ssl
import os
import psutil
import requests
EOF
echo "Done"

