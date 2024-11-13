CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    profile_image VARCHAR(200),
    currency_balance INTEGER DEFAULT 0
);

-- lasciare in questa tabela solo gatcha id collect date (metterlo come data) e infine il numero di quanti ne hai
--
CREATE TABLE IF NOT EXISTS gacha_items (
    id SERIAL PRIMARY KEY,
    gacha_id VARCHAR(50) NOT NULL,
    gacha_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    rarity VARCHAR(50),
    collected_date VARCHAR(50),
    img VARCHAR(255),
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE
);

INSERT INTO profiles (username, profile_image, currency_balance) VALUES ('player1', 'default_image_url', 100);
