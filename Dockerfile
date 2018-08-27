FROM python:3.7
MAINTAINER test test@test.com

# install phantomjs
RUN mkdir -p /opt/phantomjs \
        && cd /opt/phantomjs \
        && wget -O phantomjs.tar.bz2 https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
        && tar xavf phantomjs.tar.bz2 --strip-components 1 \
        && ln -s /opt/phantomjs/bin/phantomjs /usr/local/bin/phantomjs \
        && rm phantomjs.tar.bz2


#RUN mkdir -p /opt/freetds \
#		&& cd /opt/freetds \
#		&& wget -O freetds.tar.bz2 http://101.110.118.21/mirrors.ibiblio.org/freetds/stable/freetds-0.91.tar.bz2 \
#		&& tar xavf freetds.tar.bz2 --strip-components 1 \
#        && rm freetds.tar.bz2 \
#        && su root \ 
#        && ./configure --prefix=/usr/local/freetds --with-tdsver=8.0 --enable-msdblib \
#        && make \
#        && make install

RUN mv /etc/apt/sources.list /etc/apt/sources.list.back \
		&& echo "deb http://mirrors.163.com/debian jessie main non-free contrib \
deb http://mirrors.163.com/debian jessie-proposed-updates main contrib non-free \
deb http://mirrors.163.com/debian-security jessie/updates main contrib non-free \
deb-src http://mirrors.163.com/debian jessie main non-free contrib \
	" > /etc/apt/sources.list \
		&& apt-get update -y \
		&& apt-get autoremove \
		&& apt-get autoclean \
		&& apt-get dist-upgrade \
		&& apt-get upgrade \
		&& apt-get autoremove freetds* --purge \
		&& apt-get remove apparmor \
		&& apt-get install -y freetds-bin freetds-common freetds-dev  --fix-missing --fix-broken \
		&& apt-get install -y unixodbc unixodbc-dev


# install requirements
#RUN pip install --egg 'https://dev.mysql.com/get/Downloads/Connector-Python/mysql-connector-python-2.1.5.zip#md5=ce4a24cb1746c1c8f6189a97087f21c1'
COPY requirements.txt /opt/pyspider/requirements.txt
RUN pip3 install -i https://mirrors.aliyun.com/pypi/simple -r /opt/pyspider/requirements.txt



#install chrome 

RUN apt-get install -y libfontconfig fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libnspr4 libnss3 libxtst6 lsb-release xdg-utils libxss1 libappindicator1 libindicator7 unzip  xvfb  libgconf2-4
RUN mkdir -p /opt/chrome \
        && cd /opt/chrome \
        && wget -O google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
		&& dpkg -i google-chrome*.deb \
		&& apt-get install -f \
		&& wget -O chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/2.31/chromedriver_linux64.zip \
		&& unzip chromedriver_linux64.zip \
		&& ln -s /opt/chrome/chromedriver /usr/bin/chromedriver

# add all repo
ADD ./ /opt/pyspider

# run test
WORKDIR /opt/pyspider
RUN pip3 install -i https://mirrors.aliyun.com/pypi/simple -e .[all]

VOLUME ["/opt/pyspider"]
ENTRYPOINT ["pyspider"]

EXPOSE 5000 23333 24444 25555 9000



