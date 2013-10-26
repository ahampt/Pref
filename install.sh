#install pip
sudo apt-get install python-setuptools
sudo apt-get install python-pip
#install python dev
apt-get install python-dev
#install apache
sudo apt-get install apache2
#install mysql
sudo apt-get install mysql-server mysql-client
sudo apt-get install libmysqlclient-dev
#password 'root'
#install phpmyadmin
sudo apt-get install phpmyadmin
#install django
sudo pip install Django
#install mysql-python
pip install mysql-python
#install python-urlencoding
#install python-oauth
#install python-unicodecsv
wget https://github.com/jdunck/python-unicodecsv/archive/master.zip
unzip master.zip
cd python-unicodecsv-master
sudo python setup.py install
cd ..
sudo rm -r python-unicodecsv-master
rm master.zip
#install facebook-sdk
sudo pip install facebook-sdk
#install tweepy
sudo pip install tweepy
#install google-api-python-client
wget https://google-api-python-client.googlecode.com/files/google-api-python-client-1.2.zip
unzip google-api-python-client-1.2.zip
cd google-api-python-client-1.2
sudo python setup.py install
cd ..
sudo rm -r google-api-python-client-1.2
rm google-api-python-client-1.2.zip
#install git
sudo apt-get install git
#clone repo
git clone https://github.com/ahampt/Pref.git
# setup
cd Pref/preff
cp local_settings.template local_settings.py
# modify local settings and create log directories
