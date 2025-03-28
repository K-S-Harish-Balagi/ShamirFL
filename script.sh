#!/bin/bash

# Update package list
echo "Updating package list..."
sudo apt update -y

# Install Python3, pip
echo "Installing Python3 and pip..."
sudo apt install -y python3 python3-venv python3-pip

# Install Python packages
echo "Installing required Python packages..."
pip install numpy pandas scikit-learn tensorflow websockets phe ShamirSecret

# Verify installation
echo "Verifying installations..."
python3 -c "import numpy, pandas, tensorflow, websockets, phe, ShamirSecret; from sklearn.model_selection import train_test_split; from sklearn.preprocessing import StandardScaler, MinMaxScaler; from sklearn.metrics import mean_squared_error, r2_score; print('All modules installed successfully!')"

echo "Installation completed successfully!"
