#!/bin/bash
cd /home/ubuntu/walletrank
/usr/local/bin/python3.13 wallet_rankings.py
/usr/local/bin/python3.13 wallet_profit_loss.py
/usr/local/bin/python3.13 analyze_copy_trade_candidates.py
/usr/local/bin/python3.13 domain_wallet_rankings.py
/usr/local/bin/python3.13 analyze_domain_copy_trade_candidates.py
sudo systemctl restart lumenbro-rankings
