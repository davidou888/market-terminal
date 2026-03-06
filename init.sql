CREATE TABLE IF NOT EXISTS users (
    api_key VARCHAR(100) PRIMARY KEY NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,   
    balance DECIMAL(15,2) DEFAULT 10000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

CREATE TABLE IF NOT EXISTS order_book (
    id CHAR(36) PRIMARY KEY, 
    side CHAR(1) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    quantity DECIMAL(15,6) NOT NULL,
    user_api_key VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_api_key VARCHAR(64) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,6) DEFAULT 0,
    price DECIMAL(15,4) NOT NULL,
    UNIQUE KEY (user_api_key, symbol)
);

CREATE TABLE IF NOT EXISTS trade_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    buy_order_id VARCHAR(64),
    sell_order_id VARCHAR(64),
    /*order ids ?*/
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    quantity DECIMAL(15,6) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);