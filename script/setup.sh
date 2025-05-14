apt install build-essential uuid-dev iasl python-is-python3 git curl libglib2.0-dev libfdt-dev libpixman-1-dev zlib1g-dev ninja-build python3-venv llvm clang vim
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
echo "deb http://archive.ubuntu.com/ubuntu jammy main universe" | tee /etc/apt/sources.list.d/jammy.list
apt update
apt install -t jammy nasm
rm /etc/apt/sources.list.d/jammy.list
apt update
apt-get install python3-pip
pip install psutil
pip install r2pipe
