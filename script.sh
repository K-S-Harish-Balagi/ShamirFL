#!/bin/bash

# Update package list
echo "Updating package list..."
sudo apt update -y

# Install pip if not installed
if ! command -v pip &> /dev/null; then
    echo "pip not found! Installing..."
    sudo apt install -y python3-pip
else
    echo "pip is already installed."
fi

# Ensure pip is up-to-date
python3 -m pip install --upgrade pip

# Install required Python packages
echo "Installing required Python packages..."
if ! python3 -m pip install --break-system-packages numpy pandas websockets phe; then
    echo "❌ Package installation failed!"
    exit 1
fi

# Update PATH for locally installed binaries
echo "Updating PATH..."
echo "export PATH=$HOME/.local/bin:$PATH" >> ~/.bashrc

# Apply changes and restart the shell
echo "Restarting shell..."
exec bash

# Verify installation after restart
echo "Verifying installation..."
python3 -c "import numpy, pandas, websockets, phe; print('✅ All packages installed successfully!')"

echo "🎉 Installation complete! Your shell has been restarted."
