from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web3 import Web3

router = APIRouter()

class LoanRequest(BaseModel):
    amount: float
    interestRate: float

# Configuración de la blockchain
provider = "https://mainnet.infura.io/v3/TU_INFURA_PROJECT_ID"
private_key = "TU_CLAVE_PRIVADA"
contract_address = "DIRECCIÓN_CONTRATO"
abi = [...]  # Copia el ABI del contrato

w3 = Web3(Web3.HTTPProvider(provider))
account = w3.eth.account.from_key(private_key)
contract = w3.eth.contract(address=contract_address, abi=abi)

@router.post("/api/loans/request")
async def request_loan(request: LoanRequest):
    try:
        tx = contract.functions.requestLoan(
            int(request.amount * 1e18),  # Convertir a Wei
            int(request.interestRate)
        ).buildTransaction({
            "from": account.address,
            "nonce": w3.eth.getTransactionCount(account.address),
            "gas": 2000000,
            "gasPrice": w3.toWei("20", "gwei")
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return {"txHash": tx_hash.hex()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al solicitar préstamo: {str(e)}")
