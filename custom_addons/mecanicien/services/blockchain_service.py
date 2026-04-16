import hashlib
import uuid
import json
import os


CONTRACT_ADDRESS = "SIMULATED_BLOCKCHAIN"


def get_web3():
    return None


def get_contract():
    return None


def compute_reparation_hash(reparation):
    data = f"{reparation.id}-{reparation.name}"
    return hashlib.sha256(data.encode()).hexdigest()


def enregistrer_sur_blockchain(reparation):
    hash_value = compute_reparation_hash(reparation)

    # simulation d'un transaction hash type blockchain
    tx_hash = "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:24]

    return tx_hash, hash_value