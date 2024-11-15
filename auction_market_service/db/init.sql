-- Creazione della tabella auctions
CREATE TABLE IF NOT EXISTS auctions (
    id SERIAL PRIMARY KEY,
    gatcha_id INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    winner_id INTEGER DEFAULT NULL,
    current_bid FLOAT DEFAULT 0.0,
    base_price FLOAT NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(10) DEFAULT 'active'
);

-- Creazione della tabella users (per autenticazione e ruoli)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(10) NOT NULL -- 'user' o 'admin'
);

-- Dati di test per users
INSERT INTO users (username, role) VALUES ('admin_user', 'admin');
