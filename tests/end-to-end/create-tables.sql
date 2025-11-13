-- Création des tables pour le pipeline de données

-- Schema CRM
CREATE SCHEMA IF NOT EXISTS crm;

-- Table clients CRM
CREATE TABLE IF NOT EXISTS crm.customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    registration_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE'
);

-- Table transactions
CREATE TABLE IF NOT EXISTS crm.transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES crm.customers(customer_id),
    amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'MAD',
    transaction_type VARCHAR(20),
    timestamp TIMESTAMP,
    merchant VARCHAR(255),
    category VARCHAR(50)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_customers_status ON crm.customers(status);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON crm.transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON crm.transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON crm.transactions(transaction_type);