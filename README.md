# Crypto EMA200 Weekly Dashboard

Monitore a distancia do preco atual a EMA200 (media movel exponencial de 200 periodos) no timeframe semanal para os top 100 criptoativos.

## Arquitetura

```
                     COINGECKO API
                           |
                    (get top 200 coins)
                           |
                           v
                  STANDALONE SCRIPT
                  (Local ou Cloud)
                           |
                   +--------+--------+
                   |                 |
                   v                 v
            BINANCE API          GOOGLE SHEETS
         (weekly klines)        (data storage)
                   |                 |
                   +--------+--------+
                           |
                           v
                    STREAMLIT APP
                   (cloud or local)
                    (read-only)
```

## Como Funciona

1. **Backend (Standalone Script)**
   - Executa 1x por semana
   - Busca top 100 criptos da CoinGecko
   - Para cada cripto, fetcha 300 candles semanais da Binance
   - Calcula EMA200 e distancia percentual
   - Sincroniza dados com Google Sheets

2. **Storage (Google Sheets)**
   - Armazena snapshot de dados
   - Disponibiliza via URL publica CSV
   - Nenhuma reprocessamento necessario

3. **Frontend (Streamlit App)**
   - Carrega dados do Google Sheets CSV
   - Exibe tabela com filtros
   - Mostra rankings de sobrecomprado/sobrevendido
   - Deploy automatico em Streamlit Cloud

## Quick Start

### Opcao 1: Rodar localmente

```bash
# 1. Clonar repo
git clone https://github.com/seu-usuario/crypto-ema200
cd crypto-ema200

# 2. Criar virtual env
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements_standalone.txt
pip install -r requirements_streamlit.txt

# 4. Setup Google Sheets (veja SETUP.md)

# 5. Rodar standalone script
python standalone_script.py --sheet-id YOUR_SHEET_ID --service-account service_account.json

# 6. Rodar Streamlit app
streamlit run app.py
```

### Opcao 2: Deploy na Nuvem

```bash
# 1. Push para GitHub
git push origin main

# 2. Deploy Streamlit App em https://streamlit.io/cloud
   - Conectar repo
   - Selecionar app.py
   - Fazer deploy

# 3. Agendar standalone script em Cloud Function
   - Criar function em Python 3.9+
   - Copiar codigo do standalone_script.py
   - Agendar para rodar toda segunda-feira 00:00 UTC
   - Usar Secret Manager para service_account.json
```

## Arquivos

- `standalone_script.py`: Backend data pipeline
- `app.py`: Streamlit dashboard frontend
- `requirements_standalone.txt`: Deps backend
- `requirements_streamlit.txt`: Deps frontend
- `service_account.json`: Google Cloud credentials (NAO commitar!)

## Variables de Ambiente

```bash
GOOGLE_SHEET_ID=seu_sheet_id_aqui
GOOGLE_SERVICE_ACCOUNT=/path/to/service_account.json
```

## Interpretacao dos Dados

- **dist_pct > 0**: Preco acima da EMA200 (potencial tendencia de alta)
- **dist_pct < 0**: Preco abaixo da EMA200 (potencial tendencia de baixa)
- **dist_pct > 30%**: Sobrecomprado (potencial reversal para baixo)
- **dist_pct < -30%**: Sobrevendido (potencial reversal para cima)

## Fontes de Dados

- **Top Coins**: CoinGecko API (free)
- **Candles Semanais**: Binance Public API (free)
- **Metadata**: CoinGecko

## Tech Stack

- **Backend**: Python 3.9+
- **Libraries**: pandas, pandas_ta, requests, google-api-python-client
- **Storage**: Google Sheets
- **Frontend**: Streamlit
- **Deployment**: Streamlit Cloud, Google Cloud Functions

## Proximas Melhorias

- [ ] Adicionar mais indicadores (RSI, MACD, Bollinger Bands)
- [ ] Alertas via email quando dist > 40% ou < -40%
- [ ] Historico de EMA200 em grafico interativo
- [ ] Dados intraday alem de weekly
- [ ] Mobile-friendly design
- [ ] Database permanente (Firebase/PostgreSQL)

## Troubleshooting

**Rate limit da Binance**: Aumentar delay entre requests em `standalone_script.py`

**Google Sheets nao sincroniza**: Verificar credenciais do service account

**App Streamlit lento**: Aumentar cache TTL ou usar database ao inves de Sheets

## License

MIT
