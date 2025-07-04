import json
import time
from web3 import Web3

# Sepolia RPC
SEPOLIA_RPC = 'https://eth-sepolia.g.alchemy.com/v2/TjbQLMzPwsWwzp4fFlHnZAZbJfYqRaU7'
CONTRACT_ADDRESS = '0x3eDF60dd017aCe33A0220F78741b5581C385A1BA'
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"}
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# 读取钱包
wallets = []
with open('wallets-final.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        infos = line.split(',')
        wallets.append((infos[0], infos[1]))

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

for idx, (addr, pk) in enumerate(wallets, 1):
    try:
        account = w3.eth.account.from_key(pk)
        nonce = w3.eth.get_transaction_count(addr)
        txn = contract.functions.mint(addr).build_transaction({
            'from': addr,
            'nonce': nonce,
            'gas': 76719,
            'gasPrice': w3.eth.gas_price
        })
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=pk)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"{idx}. 钱包 {addr} 已发送mint交易，tx hash: {tx_hash.hex()}")
        #time.sleep(2)
    except Exception as e:
        print(f"钱包 {addr} 发送mint交易失败: {e}")

print('全部处理完成') 