import asyncio
import pickle
import zlib
import numpy as np
import websockets
from phe import paillier
import ShamirSecret
import socket
import requests

def get_public_ipv4():
    try:
        return requests.get('https://api4.ipify.org').text  # Ensures IPv4
    except requests.RequestException:
        return "Unable to determine public IPv4"

HOST = get_public_ipv4()
print(f"Server Public IPv4: {HOST}")


# ======= Server Parameters =======
#HOST = socket.gethostbyname(socket.gethostname()) # gets host local ip
#HOST = '127.0.0.1' # manual
PORT = 65432
THRESHOLD = 2
BIG_P = 104729  # Large prime for modular operation

public_keys = {}
ciphertexts = {}
encrypted_shares = {}
aggregated_ciphertext = None
aggregated_shares = {}
aggregation_done = False
decrypted_shares = {}
reconstruction_done = False
aggregated_shamir_secret = None
count = 0

# ======= Generate Paillier Key Pair =======
public_key, private_key = paillier.generate_paillier_keypair()

# ======= Handle Client Connection =======
async def handle_client(websocket, _=None):
    global public_keys
    
    try:
        # Receive public key from client
        data = await websocket.recv()
        data = pickle.loads(zlib.decompress(data))

        client_id = data['client_id']
        public_keys[client_id] = data['public_key']

        print(f"[SERVER] Received public key from Client {client_id}")

        # Wait until all clients send public keys
        while len(public_keys) < THRESHOLD:
            print(f"[SERVER] Waiting for all clients... ({len(public_keys)}/{THRESHOLD})")
            await asyncio.sleep(1)

        # Send server parameters to all clients
        response = {
            'public_key_server': public_key,
            'threshold': THRESHOLD,
            'p': BIG_P,
            'public_keys': public_keys
        }
        await websocket.send(zlib.compress(pickle.dumps(response)))
        print(f"[SERVER] Sent public key & parameters to Client {client_id}")

        await aggregate_weight(websocket, client_id)

    except websockets.exceptions.ConnectionClosedError:
        print(f"[SERVER] Client {client_id} disconnected unexpectedly.")
    except Exception as e:
        print(f"[SERVER] Error: {e}")


async def aggregate_weight(websocket, client_id):
    global public_keys, ciphertexts, encrypted_shares, aggregated_ciphertext, aggregated_shares, aggregation_done, decrypted_shares, reconstruction_done, aggregated_shamir_secret, count

    # Receive encrypted ciphertext and shares from client
    data = await websocket.recv()
    data = pickle.loads(zlib.decompress(data))

    ciphertexts[client_id] = data['ciphertext']
    encrypted_shares[client_id] = data['shares']

    print(f"[SERVER] Received ciphertext and shares from Client {client_id}")

    # If all clients have submitted weights and shares, aggregate them
    if len(encrypted_shares) == len(public_keys):
        
        # Aggregate encrypted local models homomorphically
        aggregated_ciphertext = np.array(ciphertexts[list(ciphertexts.keys())[0]])
        for cid in list(ciphertexts.keys())[1:]:
            aggregated_ciphertext = aggregated_ciphertext + np.array(ciphertexts[cid])
        
        print(f"[SERVER] Aggregated Ciphertext: {aggregated_ciphertext}")

        # Aggregate Shamir shares
        aggregated_shares = encrypted_shares[list(ciphertexts.keys())[0]].copy()
        for i in list(ciphertexts.keys())[1:]:
            for j in ciphertexts:
                aggregated_shares[j] = aggregated_shares[j] + encrypted_shares[i][j]  # Homomorphic Addition

        aggregation_done = True

    while not aggregation_done:
        print(f"[SERVER] Waiting for all clients to send weights... ({len(encrypted_shares)}/{len(public_keys)})")
        await asyncio.sleep(1)  # Avoid busy waiting

    # Send aggregated shares to client
    compressed_data = zlib.compress(pickle.dumps(aggregated_shares[client_id]))
    await websocket.send(compressed_data)
    print(f"[SERVER] Sent aggregated share to Client {client_id}")

    # Receive decrypted shares from clients
    data = await websocket.recv()
    data = pickle.loads(zlib.decompress(data))

    # Store the decrypted share
    decrypted_shares[client_id] = private_key.decrypt(data)

    # ======= Reconstruct Secret Using Shamir =======
    if len(decrypted_shares) == len(public_keys):
        if len(decrypted_shares) >= THRESHOLD:
            aggregated_shamir_secret = ShamirSecret.reconstruct_secret(decrypted_shares)
            print(f"[SERVER] Reconstructed Shamir Secret: {aggregated_shamir_secret}")
        reconstruction_done = True

    while not reconstruction_done:
        print(f"[SERVER] Waiting for all clients to finish decryption...")
        await asyncio.sleep(1)

    # Send final aggregated global model
    final_model = {
        'aggregated_shamir_secret': public_keys[client_id].encrypt(aggregated_shamir_secret),
        'aggregated_ciphertext': aggregated_ciphertext,
        'n': len(public_keys)
    }

    compressed_data = zlib.compress(pickle.dumps(final_model))
    await websocket.send(compressed_data)
    print(f"[SERVER] Sent Final Model to Client {client_id}")
    
    count += 1

    if count == len(public_keys):
        print("[SERVER] All clients received the final model. Resetting state...")
        # Reset state variables after all clients finish
        public_keys.clear()
        ciphertexts.clear()
        encrypted_shares.clear()
        aggregated_ciphertext = None
        aggregated_shares.clear()
        aggregation_done = False
        decrypted_shares.clear()
        reconstruction_done = False
        aggregated_shamir_secret = None
        count = 0

# ======= Start Server =======
async def main():
    server = await websockets.serve(handle_client, HOST, PORT)
    print(f"[SERVER] Server started on ws://{HOST}:{PORT}")
    await server.wait_closed()

# Run server
asyncio.run(main())
