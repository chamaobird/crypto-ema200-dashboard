
#!/usr/bin/env python3
"""
Crypto EMA200 Dashboard - Standalone Script
Executa 1x por semana para sincronizar dados com Google Sheets
Pode rodar localmente ou em Cloud Function
"""

import time
import json
from datetime import datetime, timezone
import requests
import pandas as pd
import pandas_ta as ta
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class CryptoEMA200:
    def __init__(self, google_service_account_json=None):
        """Inicializar com credenciais Google (opcional)"""
        self.binance_api = "https://api.binance.com/api/v3"
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        self.sheet_service = None
        
        if google_service_account_json:
            self._init_sheets_auth(google_service_account_json)
    
    def _init_sheets_auth(self, service_account_json):
        """Autenticar com Google Sheets"""
        try:
            credentials = Credentials.from_service_account_file(
                service_account_json,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.sheet_service = build('sheets', 'v4', credentials=credentials)
            print("[OK] Autenticacao Google Sheets")
        except Exception as e:
            print(f"[ERRO] Sheets auth: {e}")
    
    def get_top_coins(self, limit=100):
        """Buscar top coins por marketcap da CoinGecko"""
        per_page = min(limit, 250)
        page = 1
        all_rows = []
        
        while len(all_rows) < limit:
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": per_page,
                "page": page,
                "sparkline": "false",
            }
            try:
                resp = requests.get(f"{self.coingecko_api}/coins/markets", params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    break
                all_rows.extend(data)
                page += 1
                time.sleep(1)
            except Exception as e:
                print(f"[ERRO] Fetch coins: {e}")
                break
        
        df = pd.DataFrame(all_rows[:limit])
        cols = ["id", "symbol", "name", "market_cap", "current_price", "market_cap_rank"]
        return df[cols]
    
    def get_binance_weekly_klines(self, symbol, limit=300):
        """Buscar klines semanais da Binance"""
        symbol_usdt = f"{symbol.upper()}USDT"
        url = f"{self.binance_api}/klines"
        params = {"symbol": symbol_usdt, "interval": "1w", "limit": limit}
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            klines = resp.json()
            if not klines:
                return pd.DataFrame(columns=['close'])
            
            df = pd.DataFrame(klines, columns=[
                'time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            df['timestamp'] = pd.to_datetime(df['time'], unit='ms', utc=True)
            df = df.set_index('timestamp').sort_index()
            df['close'] = pd.to_numeric(df['close'])
            return df[['close']]
        except Exception as e:
            print(f"  [ERRO] {symbol_usdt}: {e}")
            return pd.DataFrame(columns=['close'])
    
    def compute_weekly_ema200(self, df_daily):
        """Calcular EMA200 semanal"""
        if df_daily.empty:
            return df_daily
        
        df_w = df_daily.resample('W-SUN').last()
        df_w = df_w.dropna(subset=['close'])
        
        if len(df_w) < 50:
            pass
        
        df_w['ema_200'] = ta.ema(df_w['close'], length=200)
        df_w['dist_pct'] = (df_w['close'] - df_w['ema_200']) / df_w['ema_200'] * 100
        return df_w
    
    def build_snapshot(self, limit_coins=100):
        """Construir snapshot de dados"""
        print(f"\n[FETCH] Buscando top {limit_coins} coins...")
        top_df = self.get_top_coins(limit_coins)
        
        mapping = {
            'bitcoin': 'BTC', 'ethereum': 'ETH', 'tether': 'USDT',
            'bnb': 'BNB', 'solana': 'SOL', 'cardano': 'ADA',
            'polkadot': 'DOT', 'dogecoin': 'DOGE', 'litecoin': 'LTC',
            'ripple': 'XRP', 'avalanche-2': 'AVAX', 'polygon': 'MATIC',
            'chainlink': 'LINK', 'uniswap': 'UNI', 'cosmos': 'ATOM',
        }
        
        records = []
        for idx, row in top_df.iterrows():
            symbol = mapping.get(row['id'])
            if not symbol:
                continue
            
            print(f"[{idx+1:3d}/{len(top_df)}] {row['symbol'].upper():8} -> {symbol:8}", end=" ")
            
            df_weekly = self.get_binance_weekly_klines(symbol, limit=300)
            if df_weekly.empty:
                print("[VAZIO]")
                continue
            
            df_weekly = self.compute_weekly_ema200(df_weekly)
            if df_weekly['ema_200'].dropna().empty:
                print("[EMA_INSUF]")
                continue
            
            last = df_weekly.dropna(subset=['ema_200']).iloc[-1]
            print(f"[OK] dist={float(last['dist_pct']):+.1f}%")
            
            records.append({
                'symbol': row['symbol'],
                'name': row['name'],
                'market_cap_rank': row['market_cap_rank'],
                'current_price': row['current_price'],
                'weekly_close': float(last['close']),
                'ema_200': float(last['ema_200']),
                'dist_pct': float(last['dist_pct']),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })
            
            time.sleep(0.5)
        
        return pd.DataFrame(records)
    
    def sync_to_sheets(self, spreadsheet_id, data_df):
        """Sincronizar dados com Google Sheets"""
        if not self.sheet_service:
            print("[ERRO] Sheet service nao inicializado")
            return False
        
        try:
            # Limpar sheet anterior
            self.sheet_service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range='Sheet1'
            ).execute()
            
            # Escrever header
            header = list(data_df.columns)
            values = [header] + data_df.values.tolist()
            
            body = {'values': values}
            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"[OK] {len(data_df)} registros sincronizados para Sheets")
            return True
        except Exception as e:
            print(f"[ERRO] Sync sheets: {e}")
            return False

# Uso principal
if __name__ == "__main__":
    # Instancia
    crypto = CryptoEMA200(
        google_service_account_json="/path/to/service_account.json"  # Opcional
    )
    
    # Executar pipeline
    snapshot = crypto.build_snapshot(limit_coins=100)
    
    # Salvar local
    snapshot.to_csv("crypto_ema200_latest.csv", index=False)
    print(f"\n[SALVO] {len(snapshot)} moedas em crypto_ema200_latest.csv")
    
    # Opcional: sincronizar com Google Sheets
    # crypto.sync_to_sheets(spreadsheet_id="YOUR_SHEET_ID", data_df=snapshot)
