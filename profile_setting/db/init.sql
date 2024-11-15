CREATE TABLE IF NOT EXISTS profiles (
    username VARCHAR(50) PRIMARY KEY,
    profile_image VARCHAR(200),
    currency_balance INTEGER DEFAULT 0
);

-- lasciare in questa tabela solo gatcha id collect date (metterlo come data) e infine il numero di quanti ne hai
--
CREATE TABLE IF NOT EXISTS gacha_items (
    gacha_name VARCHAR(50) NOT NULL,
    collected_date TIMESTAMP NOT NULL,
    username VARCHAR(50) REFERENCES profiles(username) ON DELETE CASCADE,
    PRIMARY KEY (gacha_name,collected_date)
);

-- INSERT INTO profiles (username, profile_image, currency_balance) VALUES ('player1', 'default_image_url', 100);
