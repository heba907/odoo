import hashlib
import json
import os

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

CONTRACT_ADDRESS = "0x2b32e3677BC816A68e4fd17823a472cAb5D186A0"


def get_web3():
    rpc_url = os.getenv("ALCHEMY_URL")
    return Web3(Web3.HTTPProvider(rpc_url))


def get_contract():
    web3 = get_web3()

    abi_path = os.path.join(
        os.path.dirname(__file__),
        "GarageRegistry_abi.json"
    )

    with open(abi_path, "r") as f:
        abi = json.load(f)

    return web3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=abi
    )


def compute_reparation_hash(reparation):
    data = f"{reparation.id}-{reparation.name}"
    return hashlib.sha256(data.encode()).hexdigest()


def enregistrer_sur_blockchain(reparation):
    hash_value = compute_reparation_hash(reparation)

    # temporaire : test de connexion
    tx_hash = "CONNECTED_TO_SEPOLIA"

    return tx_hash, hash_value