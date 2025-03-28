#!/bin/bash

# Update package list
echo "Updating package list..."
sudo apt update -y

sudo apt install -y python3-pip

echo "Installing required Python packages..."
pip install --break-system-packages numpy pandas websockets phe 

echo "Updating PATH for locally installed binaries..."
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

echo "Verifying installation..."
python3 -c "import numpy, pandas, tensorflow, websockets, phe, sklearn; print('All packages installed successfully!')"

echo "Installation complete!"
