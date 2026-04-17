import hashlib
import json
import os

from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

load_dotenv()

# -------------------------------
# Configuration blockchain
# -------------------------------
ALCHEMY_URL = "https://eth-sepolia.g.alchemy.com/v2/5o2XwcmfG72rabO7lxuKV"

PRIVATE_KEY = "9fd1d9fae7f5594bcdedd34af5dac7a6d15c5172bd27f6d366a0f501d7e67b58"

CONTRACT_ADDRESS = "0x68f691462d7864d2f0252F6d4fe9C1C4fD907920"

CHAIN_ID = 11155111  # Sepolia


ABI_PATH = os.path.join(
    os.path.dirname(__file__),
    "GarageRegistry_abi.json"
)


# -------------------------------
# Connexion Web3
# -------------------------------
def get_web3():
    web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

    if not web3.is_connected():
        raise Exception("Impossible de se connecter à Sepolia")

    return web3


# -------------------------------
# Smart contract
# -------------------------------
def get_contract():
    web3 = get_web3()

    with open(ABI_PATH, "r") as f:
        abi = json.load(f)

    return web3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=abi
    )


# -------------------------------
# Hash réparation
# -------------------------------
def compute_reparation_hash(reparation):
    data = f"{reparation.id}-{reparation.name}"
    return hashlib.sha256(data.encode()).hexdigest()


# -------------------------------
# Envoi blockchain
# -------------------------------
def enregistrer_sur_blockchain(reparation):
    web3 = get_web3()
    contract = get_contract()

    hash_value = compute_reparation_hash(reparation)

    account = Account.from_key(PRIVATE_KEY)
    wallet_address = account.address

    nonce = web3.eth.get_transaction_count(wallet_address)

    tx = contract.functions.storeRepair(
        reparation.id,
        hash_value
    ).build_transaction({
        "from": wallet_address,
        "nonce": nonce,
        "gas": 200000,
        "gasPrice": web3.eth.gas_price,
        "chainId": CHAIN_ID
    })

    signed_tx = web3.eth.account.sign_transaction(
        tx,
        private_key=PRIVATE_KEY
    )

    tx_hash = web3.eth.send_raw_transaction(
        signed_tx.raw_transaction
    )

    return tx_hash.hex(), hash_value