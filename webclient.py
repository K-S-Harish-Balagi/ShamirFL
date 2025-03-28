import asyncio
import pickle
import zlib
import numpy as np
import websockets
from phe import paillier
import ShamirSecret

# ======= Client Parameters =======
HOST = 'ws://127.0.0.1'
PORT = 65432
client_id = int(input("Enter Client ID: "))
num_weights = 3  # Default Parameter

# ======= Generate Paillier Key Pair =======
public_key, secret_key = paillier.generate_paillier_keypair()

# ======= Server Parameters =======
THRESHOLD = None
BIG_P = None

public_keys = None
public_key_server = None


# ======= Initialize =======
async def initialize():
    uri = f"{HOST}:{PORT}"
    async with websockets.connect(uri) as websocket:
        # Send public key to server
        data = {
            'client_id': client_id,
            'public_key': public_key
        }
        compressed_data = zlib.compress(pickle.dumps(data))
        await websocket.send(compressed_data)
        print(f"[CLIENT {client_id}] Sent public key to server")

        global THRESHOLD, BIG_P, public_keys, public_key_server

        # Receive server key and parameters
        response = await websocket.recv()
        data = pickle.loads(zlib.decompress(response))

        public_key_server = data['public_key_server']
        THRESHOLD = data['threshold']
        BIG_P = data['p']
        public_keys = data['public_keys']

        await aggregate_weight(websocket)


async def aggregate_weight(websocket):
    # ======= Generate Local Model =======
    local_weights = np.random.randint(1, 10, num_weights)
    print(f"[CLIENT {client_id}] Local Weights: {local_weights}")

    # ======= Generate masking value =======
    shamir_secret = np.random.randint(1, BIG_P - 1)
    print(f"[CLIENT {client_id}] Shamir Secret Key: {shamir_secret}")

    # ======= Encrypt Weights =======
    ciphertext = [w + shamir_secret for w in local_weights]

    # ======= Generate Shamir Secret Shares =======
    shares = ShamirSecret.generate_share(shamir_secret, list(public_keys.keys()), THRESHOLD)

    # Encrypt and store shares
    encrypted_shares = {
        cid: public_keys[cid].encrypt(shares[cid])
        for cid in public_keys
    }

    # Compress and send encrypted ciphertext and shares to server
    data = {
        'ciphertext': ciphertext,
        'shares': encrypted_shares
    }
    compressed_data = zlib.compress(pickle.dumps(data))
    await websocket.send(compressed_data)
    print(f"[CLIENT {client_id}] Sent ciphertext and encrypted shares to server")

    # Receive Aggregated Share from Server
    response = await websocket.recv()
    aggregated_share = pickle.loads(zlib.decompress(response))

    # Decrypt aggregated share using secret key
    decrypted_share = secret_key.decrypt(aggregated_share)

    # Re-encrypt with server's public key before sending back
    encrypted_decrypted_share = public_key_server.encrypt(decrypted_share)

    # Send back encrypted share to server
    compressed_data = zlib.compress(pickle.dumps(encrypted_decrypted_share))
    await websocket.send(compressed_data)
    print(f"[CLIENT {client_id}] Sent decrypted share to server")

    # ======= Receive Final Aggregated Global Model =======
    response = await websocket.recv()
    data = pickle.loads(zlib.decompress(response))

    aggregated_shamir_secret = secret_key.decrypt(data['aggregated_shamir_secret'])
    aggregated_ciphertext = data['aggregated_ciphertext']
    n = data['n']

    # Compute final model after unmasking
    final_weights = [(ct - aggregated_shamir_secret) / n for ct in aggregated_ciphertext]
    print(f"[CLIENT {client_id}] Final Aggregated Model: {final_weights}")

    print(f"[CLIENT {client_id}] Training and aggregation complete. Exiting.")


# Start client connection
asyncio.run(initialize())
