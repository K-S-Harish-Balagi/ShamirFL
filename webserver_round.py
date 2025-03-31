import asyncio
import pickle
import zlib
import numpy as np
import websockets
from phe import paillier
import ShamirSecret
import requests

# Get public IPv4 address
def get_public_ipv4():
    try:
        return requests.get('https://api4.ipify.org').text
    except requests.RequestException:
        return "Unable to determine public IPv4"

HOST = get_public_ipv4()
PORT = 65432
THRESHOLD = 2
BIG_P = 104729  # Large prime for modular operation

# Global variables (reset per round)
public_keys = {}
ciphertexts = {}
encrypted_shares = {}
decrypted_shares = {}
aggregated_ciphertext = None
aggregated_shamir_secret = None
count = 0

# Generate Paillier Key Pair
public_key, private_key = paillier.generate_paillier_keypair()

# Handle client connection
async def handle_client(websocket, _=None):
    global public_keys

    try:
        # Receive public key from client
        data = await websocket.recv()
        data = pickle.loads(zlib.decompress(data))
        client_id = data['client_id']
        public_keys[client_id] = data['public_key']
        print(f"[SERVER] Received public key from Client {client_id}")

        # Wait for all clients
        while len(public_keys) < THRESHOLD:
            print(f"[SERVER] Waiting for all clients... ({len(public_keys)}/{THRESHOLD})")
            await asyncio.sleep(1)

        # Send server parameters
        response = {
            'public_key_server': public_key,
            'threshold': THRESHOLD,
            'p': BIG_P,
            'public_keys': public_keys
        }
        await websocket.send(zlib.compress(pickle.dumps(response)))
        print(f"[SERVER] Sent parameters to Client {client_id}")

        # **Main training loop**
        while True:
            keep_going = await aggregate_weight(websocket, client_id)
            if not keep_going:
                print(f"[SERVER] Client {client_id} has finished training.")
                break  # Stop receiving from this client

    except websockets.exceptions.ConnectionClosedError:
        print(f"[SERVER] Client {client_id} disconnected unexpectedly.")
    except Exception as e:
        print(f"[SERVER] Error: {e}")

async def aggregate_weight(websocket, client_id):
    global ciphertexts, encrypted_shares, aggregated_ciphertext, decrypted_shares, aggregated_shamir_secret, count

    # Receive encrypted ciphertext and shares from client
    data = await websocket.recv()
    data = pickle.loads(zlib.decompress(data))

    # Stop condition
    if data.get("stop"):
        return False  

    ciphertexts[client_id] = data['ciphertext']
    encrypted_shares[client_id] = data['shares']
    print(f"[SERVER] Received ciphertext and shares from Client {client_id}")

    # Wait for all clients
    while len(encrypted_shares) < len(public_keys):
        print(f"[SERVER] Waiting for all clients... ({len(encrypted_shares)}/{len(public_keys)})")
        await asyncio.sleep(1)

    # **Efficient NumPy-based ciphertext aggregation**
    ciphertext_array = np.array(list(ciphertexts.values()))  
    aggregated_ciphertext = np.sum(ciphertext_array, axis=0) % ShamirSecret.PRIME_Q  

    print(f"[SERVER] Aggregated Ciphertext: {aggregated_ciphertext}")

    # **Aggregate Shamir shares**
    aggregated_shares = {}
    for client in encrypted_shares.keys():
        for j in encrypted_shares[client]:
            aggregated_shares[j] = aggregated_shares.get(j, 0) + encrypted_shares[client][j]

    # Send aggregated share to client
    await websocket.send(zlib.compress(pickle.dumps(aggregated_shares[client_id])))
    print(f"[SERVER] Sent aggregated share to Client {client_id}")

    # **Receive decrypted shares from client**
    data = await websocket.recv()
    data = pickle.loads(zlib.decompress(data))
    decrypted_shares[client_id] = private_key.decrypt(data)

    # **Reconstruct Shamir secret when enough shares are received**
    if len(decrypted_shares) >= THRESHOLD:
        aggregated_shamir_secret = ShamirSecret.reconstruct_secret(decrypted_shares)
        print(f"[SERVER] Reconstructed Shamir Secret: {aggregated_shamir_secret}")

    # **Send final aggregated global model**
    final_model = {
        'aggregated_shamir_secret': public_keys[client_id].encrypt(aggregated_shamir_secret),
        'aggregated_ciphertext': aggregated_ciphertext,
        'n': len(public_keys)
    }
    await websocket.send(zlib.compress(pickle.dumps(final_model)))
    print(f"[SERVER] Sent Final Model to Client {client_id}")

    count += 1

    # **Reset for next round**
    if count == len(public_keys):
        ciphertexts.clear()
        encrypted_shares.clear()
        aggregated_ciphertext = None
        decrypted_shares.clear()
        aggregated_shamir_secret = None
        count = 0
        print("[SERVER] Round complete. Ready for next round.")

    return True  # Continue to next round

# Start server
async def main():
    server = await websockets.serve(handle_client, HOST, PORT)
    print(f"[SERVER] Server started on ws://{HOST}:{PORT}")
    await server.wait_closed()

asyncio.run(main())
