# PostgreSQL Setup Guide

## Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Configuration
```bash
# Create database
sudo -u postgres createdb ai_co

# Create user (optional)
sudo -u postgres createuser --interactive
```

## Connection Test
```bash
psql -h localhost -d ai_co -U postgres
```
