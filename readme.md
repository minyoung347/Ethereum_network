# Ethereum DAO Hard Fork Network Analysis

This repository contains the code and processed data required to reproduce
the analyses and figures reported in:

"Assessing external shocks in decentralized systems:
Network analysis of Ethereum user behavior"

## Data source

Ethereum blocks and transactions were obtained from the Google BigQuery
Ethereum Public Dataset for August 7, 2015–December 31, 2016.

## Requirements

- Python 3.11
- uv
- Snakemake 7.32.4
- NetworkX
- igraph
- pandas
- statsmodels
- powerlaw

## Installation

```bash
git clone ...
cd Ethereum_network_gpu
uv sync