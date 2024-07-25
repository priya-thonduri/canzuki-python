#!/bin/bash

cd /tmp
#git clone https://github.com/priya-thonduri/canzuki-python.git
mkdir canzuki-python; cd canzuki-python
wget https://poc.canzuki.com/files/python3124.tbz
wget https://poc.canzuki.com/files/canzuki-agents.tbz

cd /
tar -xjvf /tmp/canzuki-python/python3124.tbz
cd /opt/canzuki
tar -xjvf tmp/canzuki-python/canzuki-agents.tbz
cd /

export LD_LIBRARY_PATH=/opt/canzuki/python/3.12.4/lib
/opt/canzuki/python/3.12.4/bin/python -V
if [ $? -eq 0 ]; then
	echo Python successfully installed
else
 rm -fr /tmp/canzuki-python
 echo Error. Aborting
 exit 2
fi
cp /tmp/canzuki-python/*.py /opt/canzuki

if [ `crontab -l|grep -v "^#"|grep -c "python.*canzuki.*py"` -gt 0 ]; then
	echo Cron job already exists for canzuki.
else
  echo Setting up cron.
  crontab -l > /tmp/cron.$$
  cat << EOF >> /tmp/cron.$$
*/5 * * * * [ \`ps -ef|grep -c "canzuki[A]gent"\` -lt 3 ] && ( ( LD_LIBRARY_PATH=/opt/canzuki/python/3.12.4/lib /opt/canzuki/python/3.12.4/bin/python /opt/canzuki/canzukiAgent.py >> /opt/canzuki/logs/canzukiAgent.log 2>&1 )  & )
EOF
  crontab /tmp/cron.$$
  \rm /tmp/cron.$$
fi
rm -fr /tmp/canzuki-python
echo "Cron Job:"
crontab -l|grep -v "^#"|grep "python.*canzuki.*py"

