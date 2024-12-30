const express = require("express");
const { ethers } = require("ethers");
const router = express.Router();

const provider = new ethers.providers.JsonRpcProvider("https://YOUR_RPC_PROVIDER_URL");
const wallet = new ethers.Wallet("YOUR_PRIVATE_KEY", provider);
const contractAddress = "YOUR_CONTRACT_ADDRESS";
const abi = [
    // Inserta aquí el ABI de tu contrato inteligente
];
const contract = new ethers.Contract(contractAddress, abi, wallet);

router.post("/request-loan", async (req, res) => {
    const { amount, interestRate } = req.body;
    try {
        const tx = await contract.requestLoan(amount, interestRate);
        await tx.wait();
        res.status(200).send({ message: "Loan request submitted", txHash: tx.hash });
    } catch (error) {
        res.status(500).send({ error: error.message });
    }
});

module.exports = router;
