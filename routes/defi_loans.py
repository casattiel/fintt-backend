from fastapi import APIRouter, HTTPException
from web3 import Web3

router = APIRouter()

# Configuración
provider = "https://mainnet.infura.io/v3/<YOUR_PROJECT_ID>"  # Reemplaza <YOUR_PROJECT_ID>
contract_address = "0xYourContractAddressHere"  # Dirección del contrato
private_key = "YourPrivateKeyHere"  # Clave privada del propietario
abi = [  # ABI del contrato (puedes obtenerla en Remix tras compilar el contrato)
    {
        "inputs": [
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "uint256", "name": "_interestRate", "type": "uint256"}
        ],
        "name": "requestLoan",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
        "name": "payLoan",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Inicialización de conexión
w3 = Web3(Web3.HTTPProvider(provider))
contract = w3.eth.contract(address=contract_address, abi=abi)

@router.post("/request-loan")
def request_loan(amount: float, interest_rate: float):
    try:
        account = w3.eth.account.from_key(private_key)
        tx = contract.functions.requestLoan(
            int(amount * 1e18),  # Convertir a Wei
            int(interest_rate)
        ).buildTransaction({
            "from": account.address,
            "nonce": w3.eth.getTransactionCount(account.address),
            "gas": 2000000,
            "gasPrice": w3.toWei("20", "gwei")
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return {"tx_hash": tx_hash.hex()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
