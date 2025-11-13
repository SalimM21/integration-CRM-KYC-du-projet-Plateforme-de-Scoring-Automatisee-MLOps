-- Données de test pour Transactions
INSERT INTO crm.transactions (transaction_id, customer_id, amount, currency, transaction_type, timestamp, merchant, category) VALUES
('TXN001', 'CUST001', 1500.00, 'MAD', 'DEBIT', '2024-11-01 10:30:00', 'Marjane Supermarket', 'GROCERIES'),
('TXN002', 'CUST002', 250.00, 'MAD', 'DEBIT', '2024-11-01 14:15:00', 'Pharmacie Centrale', 'HEALTHCARE'),
('TXN003', 'CUST003', 5000.00, 'MAD', 'CREDIT', '2024-11-01 16:45:00', 'Bank Transfer', 'TRANSFER'),
('TXN004', 'CUST001', 320.00, 'MAD', 'DEBIT', '2024-11-02 09:20:00', 'Café Clock', 'FOOD'),
('TXN005', 'CUST004', 1200.00, 'MAD', 'DEBIT', '2024-11-02 11:10:00', 'Total Station', 'FUEL'),
('TXN006', 'CUST005', 850.00, 'MAD', 'DEBIT', '2024-11-02 13:30:00', 'Zara Store', 'CLOTHING'),
('TXN007', 'CUST002', 75.00, 'MAD', 'DEBIT', '2024-11-03 08:45:00', 'Bakery Hassan', 'FOOD'),
('TXN008', 'CUST006', 2200.00, 'MAD', 'DEBIT', '2024-11-03 15:20:00', 'Electronics Store', 'ELECTRONICS'),
('TXN009', 'CUST007', 150.00, 'MAD', 'DEBIT', '2024-11-03 17:10:00', 'Internet Provider', 'UTILITIES'),
('TXN010', 'CUST008', 3000.00, 'MAD', 'CREDIT', '2024-11-04 12:00:00', 'Salary Deposit', 'INCOME'),
('TXN011', 'CUST003', 450.00, 'MAD', 'DEBIT', '2024-11-04 14:30:00', 'Restaurant Al Fassia', 'FOOD'),
('TXN012', 'CUST009', 180.00, 'MAD', 'DEBIT', '2024-11-05 10:15:00', 'Gym Fitness', 'HEALTHCARE'),
('TXN013', 'CUST001', 2800.00, 'MAD', 'DEBIT', '2024-11-05 16:00:00', 'Hotel Royal', 'TRAVEL'),
('TXN014', 'CUST010', 95.00, 'MAD', 'DEBIT', '2024-11-06 09:45:00', 'Coffee Shop', 'FOOD'),
('TXN015', 'CUST005', 650.00, 'MAD', 'DEBIT', '2024-11-06 13:20:00', 'Bookstore', 'EDUCATION');
