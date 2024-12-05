CREATE TABLE IF NOT EXISTS memes (
    gacha_id SERIAL PRIMARY KEY,
    meme_name VARCHAR(50) UNIQUE NOT NULL,
    image_path VARCHAR(200) NOT NULL,
    rarity VARCHAR(50) NOT NULL,
    description VARCHAR(100)
);

INSERT INTO memes (meme_name, image_path, rarity, description) VALUES
('Dancing Coffin', '/app/static/uploads/DancingCoffin.jpg', 'rare', 'Dance of the Ghanaian coffin carriers.'),
('Skinner Reaction', '/app/static/uploads/SkinnerReaction.jpg', 'common', 'Simple and immediate reaction.'),
('Doge meme with glasses', '/app/static/uploads/dogeGlasses.jpg', 'legendary', 'Doge with sunglasses, radiating coolness.'),
('Messi', '/app/static/uploads/Messi.jpg', 'common', 'Lionel Messi in iconic or funny moments.'),
('Woman vs Cat', '/app/static/uploads/WomanCat.jpg', 'rare', 'A woman yelling at a confused cat at a table.'),
('Disaster Girl', '/app/static/uploads/DisasterGirl.jpg', 'legendary', 'A little girl smiling evilly in front of a burning house.'),
('Pablo Escobar', '/app/static/uploads/Pablo.jpeg', 'common', 'Pablo in melancholic or bored moods.'),
('Chloe Confused', '/app/static/uploads/Chloe.jpg', 'rare', 'A little blonde girl with buck teeth and a confused face.'),
('Distracted Boyfriend', '/app/static/uploads/DistractedBoyfriend.jpg', 'common', 'A man turning away from his girlfriend to another woman.'),
('Doge meme', '/app/static/uploads/Doge-meme.jpg', 'legendary', 'The original Doge.');
