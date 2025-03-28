# ShamirFL - Shamir Secret Sharing in Federated Learning

ShamirFL is a secure federated learning framework that utilizes **Shamir's Secret Sharing** and **Paillier Homomorphic Encryption** to ensure privacy-preserving model aggregation. This template currently uses random numbers and can be further improved by integrating a machine learning or deep learning model.

## Features
- Secure aggregation of local models using **Paillier Homomorphic Encryption**.
- Privacy-preserving secret sharing with **Shamir's Secret Sharing**.
- Client-server architecture using **WebSockets (asyncio + websockets)**.
- Modular design for easy integration of machine learning models.
- Efficient encryption, communication, and decryption for federated learning.

## Requirements
Ensure you have Python 3.8+ installed and the following dependencies:

```bash
pip install numpy phe websockets
```

Additionally, you may need to install any missing dependencies related to Shamir's Secret Sharing (if a specific library is used).

## Installation
1. Clone the repository:

```bash
git clone https://github.com/your-username/ShamirFL.git
cd ShamirFL
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage
### Start the Server
Run the following command to start the federated learning server:

```bash
python server.py
```

### Start a Client
Each client should run separately. Start a client with:

```bash
python client.py
```

The client will:
1. Generate and send its **Paillier public key**.
2. Encrypt a random weight (currently a placeholder for ML model weights).
3. Share encrypted **Shamir Secret Shares**.
4. Aggregate and send the encrypted weights.
5. Receive the final global model.

## How It Works
1. **Key Exchange**: The server and clients exchange **Paillier public keys**.
2. **Local Model Encryption**: Each client encrypts its local weights.
3. **Secret Sharing**: Shamir's Secret Sharing is used to securely distribute shares.
4. **Secure Aggregation**: The server performs homomorphic aggregation of weights.
5. **Decryption & Model Update**: Clients decrypt the aggregated model and retrieve the updated global model.

## Future Improvements
- Integrate a **real ML/DL model** instead of placeholder random numbers.
- Implement **asynchronous secure multi-party computation**.
- Optimize encryption and communication efficiency.
- Enhance error handling and security measures.

## Contributing
We welcome contributions! Feel free to:
- Open an issue for bug reports or feature requests.
- Submit a pull request with improvements.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For questions or collaborations, reach out via GitHub Issues or email.
