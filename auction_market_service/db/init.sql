-- Creazione della tabella auctions
CREATE TABLE IF NOT EXISTS auctions (
    id SERIAL PRIMARY KEY,
    gacha_name VARCHAR(50) NOT NULL,
    seller_username VARCHAR(50) NOT NULL,
    winner_username VARCHAR(50) DEFAULT NULL,
    current_bid FLOAT DEFAULT 0.0,
    base_price FLOAT NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(10) DEFAULT 'active'
);

-- Creazione della tabella bids
CREATE TABLE IF NOT EXISTS bids (
    id SERIAL PRIMARY KEY,
    auction_id INTEGER NOT NULL,
    username  VARCHAR(50) NOT NULL,
    bid_amount FLOAT NOT NULL,
    bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (auction_id) REFERENCES auctions(id) ON DELETE CASCADE
);
-- Creazione della tabella users (per autenticazione e ruoli)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(10) NOT NULL -- 'user' o 'admin'
);

-- Dati di test per users
-- INSERT INTO users (username, role) VALUES ('admin_user', 'admin');
