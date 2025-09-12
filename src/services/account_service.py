"""
account_service.py
Account bilgileri, balance ve asset yönetimi için servis modülü.
"""

import logging
import os
import sys

# Import centralized paths and client service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .client_service import prepare_client
except ImportError:
    from client_service import prepare_client


def get_account_data(client=None):
    if client is None:
        client = prepare_client()
    
    try:
        account_info = client.get_account()
        return account_info
    except Exception as e:
        logging.error(f"Error getting account data: {e}")
        logging.exception("Full traceback for account data error:")
        raise


def retrieve_usdt_balance(client=None):
    if client is None:
        client = prepare_client()
    
    try:
        account_info = get_account_data(client)
        
        for balance in account_info['balances']:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                return usdt_balance
        
        # USDT bulunamadıysa 0 döndür
        logging.warning("USDT balance not found, returning 0")
        return 0.0
        
    except Exception as e:
        error_msg = f"Error retrieving USDT balance: {e}"
        print(error_msg)
        logging.error(error_msg)
        logging.exception("Full traceback for USDT balance error:")
        raise


def get_amountOf_asset(client, SYMBOL):
    try:
        if SYMBOL.endswith('USDT'):
            BASE_ASSET = SYMBOL[:-4]
        elif SYMBOL.endswith('BTC'):
            BASE_ASSET = SYMBOL[:-3]
        elif SYMBOL.endswith('ETH'):
            BASE_ASSET = SYMBOL[:-3]
        else:
            BASE_ASSET = SYMBOL
        
        account_info = get_account_data(client)
        
        for balance in account_info['balances']:
            if balance['asset'] == BASE_ASSET:
                asset_amount = float(balance['free'])
                logging.info(f"{BASE_ASSET} balance: {asset_amount}")
                return asset_amount
                
        logging.warning(f"{BASE_ASSET} balance not found, returning 0")
        return 0.0
        
    except Exception as e:
        error_msg = f"Error getting {SYMBOL} asset amount: {e}"
        print(error_msg)
        logging.error(error_msg)
        logging.exception(f"Full traceback for {SYMBOL} asset amount error:")
        raise





if __name__ == "__main__":
    """Test account service functions"""
    print("🚀 Testing Account Service")
    print("=" * 30)
    
    try:
        # Test USDT balance
        usdt_balance = retrieve_usdt_balance()
        print(f"💰 USDT Balance: {usdt_balance}")
        
        print("\n✅ Account service test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
