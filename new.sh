echo "这是一个一键安装ollama和open-webui并部署Deepseek r1 70b的安装脚本                    请使用JubyterLab运行该脚本"
echo "更新系统并安装依赖ing"
apt-get update && apt-get upgrade -y
apt-get install -y wget curl git pciutils lshw
echo"在数据盘创建模型存储文件夹ing"
cd /root/autodl-tmp/
mkdir ollama
cd ollama
mkdir models
echo"安装ollama"
curl -fsSL https://ollama.com/install.sh | sh
ollama serve > /dev/null 2>&1 &
cd /root/.ollama
rm -rf models
echo"将模型下载目录软连接到数据盘"
In /root/autodl-tmp/ollama/models /root/.ollama/ -s
echo"下载模型"
echo"少女祈祷中"
ollama run deepseek-r1:70b
/bye
echo"开始安装open-webui"
pip install open-webui
echo "开始安装 vits..." 
git clone https://ghproxy.net/https://github.com/jaywalnut310/vits.git  
cd vits 
pip install -r requirements.txt  
cd ..
echo "开始安装 so-vits..." 
git clone https://ghproxy.net/https://github.com/svc-develop-team/so-vits-svc.git  
cd so-vits-svc 
pip install -r requirements.txt  
cd .. 
echo "我 好 了！"
