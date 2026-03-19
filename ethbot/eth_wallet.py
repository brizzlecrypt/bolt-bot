"""
Ethereum Wallet Manager
Handles wallet generation, imports, and basic Ethereum operations
"""

from eth_account import Account
from web3 import Web3
import secrets
import json
from typing import Dict, Optional
from mnemonic import Mnemonic

class EthereumWallet:
    """Manage Ethereum wallets and interactions"""
    
    def __init__(self, rpc_url="https://eth.llamarpc.com"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.mnemo = Mnemonic("english")
        
    def generate_wallet(self) -> Dict:
        """
        Generate a new Ethereum wallet with mnemonic phrase
        Returns: {
            'address': wallet address,
            'private_key': private key (hex),
            'mnemonic': 12-word recovery phrase
        }
        """
        # Generate mnemonic (12 words)
        mnemonic_phrase = self.mnemo.generate(strength=128)
        
        # Enable HD wallet features
        Account.enable_unaudited_hdwallet_features()
        
        # Create account from mnemonic
        account = Account.from_mnemonic(mnemonic_phrase)
        
        return {
            'address': account.address,
            'private_key': account.key.hex(),
            'mnemonic': mnemonic_phrase
        }
    
    def import_from_private_key(self, private_key: str) -> Dict:
        """
        Import wallet from private key
        Args:
            private_key: Private key (with or without 0x prefix)
        Returns: {
            'success': bool,
            'address': wallet address,
            'error': error message if failed
        }
        """
        try:
            # Add 0x prefix if not present
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            # Create account from private key
            account = Account.from_key(private_key)
            
            return {
                'success': True,
                'address': account.address,
                'private_key': private_key
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_from_mnemonic(self, mnemonic_phrase: str) -> Dict:
        """
        Import wallet from mnemonic phrase
        Args:
            mnemonic_phrase: 12 or 24 word recovery phrase
        Returns: {
            'success': bool,
            'address': wallet address,
            'private_key': private key,
            'error': error message if failed
        }
        """
        try:
            # Validate mnemonic
            if not self.mnemo.check(mnemonic_phrase):
                return {
                    'success': False,
                    'error': 'Invalid mnemonic phrase'
                }
            
            # Enable HD wallet features
            Account.enable_unaudited_hdwallet_features()
            
            # Create account from mnemonic
            account = Account.from_mnemonic(mnemonic_phrase)
            
            return {
                'success': True,
                'address': account.address,
                'private_key': account.key.hex(),
                'mnemonic': mnemonic_phrase
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_balance(self, address: str) -> Dict:
        """
        Get ETH balance for an address
        Args:
            address: Ethereum address
        Returns: {
            'success': bool,
            'balance_eth': balance in ETH,
            'balance_wei': balance in Wei,
            'error': error message if failed
        }
        """
        try:
            # Validate address
            if not self.w3.is_address(address):
                return {
                    'success': False,
                    'error': 'Invalid Ethereum address'
                }
            
            # Get balance in Wei
            balance_wei = self.w3.eth.get_balance(address)
            
            # Convert to ETH
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            return {
                'success': True,
                'balance_eth': float(balance_eth),
                'balance_wei': balance_wei
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_token_balance(self, wallet_address: str, token_address: str) -> Dict:
        """
        Get ERC20 token balance
        Args:
            wallet_address: Wallet address to check
            token_address: ERC20 token contract address
        Returns: token balance info
        """
        try:
            # ERC20 ABI for balanceOf function
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }
            ]
            
            # Create contract instance
            contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            # Get balance
            balance = contract.functions.balanceOf(
                self.w3.to_checksum_address(wallet_address)
            ).call()
            
            # Get decimals and symbol
            try:
                decimals = contract.functions.decimals().call()
                symbol = contract.functions.symbol().call()
            except:
                decimals = 18
                symbol = "UNKNOWN"
            
            # Convert balance
            balance_readable = balance / (10 ** decimals)
            
            return {
                'success': True,
                'balance': balance_readable,
                'balance_raw': balance,
                'symbol': symbol,
                'decimals': decimals
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_eth(self, from_private_key: str, to_address: str, amount_eth: float) -> Dict:
        """
        Send ETH to an address
        Args:
            from_private_key: Sender's private key
            to_address: Recipient address
            amount_eth: Amount in ETH to send
        Returns: transaction info
        """
        try:
            # Add 0x prefix if needed
            if not from_private_key.startswith('0x'):
                from_private_key = '0x' + from_private_key
            
            # Create account
            account = Account.from_key(from_private_key)
            
            # Convert amount to Wei
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': self.w3.to_checksum_address(to_address),
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, from_private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'explorer_url': f'https://etherscan.io/tx/{tx_hash.hex()}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_address(self, address: str) -> bool:
        """
        Validate if string is a valid Ethereum address
        Args:
            address: String to validate
        Returns: Boolean
        """
        return self.w3.is_address(address)
    
    def get_transaction_history(self, address: str, limit: int = 10) -> Dict:
        """
        Get recent transactions for an address
        Note: This requires Etherscan API or similar service
        This is a placeholder that shows the structure
        """
        # In production, you'd use Etherscan API or Alchemy
        return {
            'success': True,
            'transactions': [],
            'message': 'Requires Etherscan API key for full implementation'
        }

# Example usage
if __name__ == '__main__':
    wallet_manager = EthereumWallet()
    
    # Generate new wallet
    print("Generating new wallet...")
    new_wallet = wallet_manager.generate_wallet()
    print(f"Address: {new_wallet['address']}")
    print(f"Private Key: {new_wallet['private_key'][:20]}...")
    print(f"Mnemonic: {new_wallet['mnemonic']}")
    
    # Check balance
    print(f"\nChecking balance...")
    balance = wallet_manager.get_balance(new_wallet['address'])
    if balance['success']:
        print(f"Balance: {balance['balance_eth']} ETH")
