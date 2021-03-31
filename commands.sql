CREATE TABLE IF NOT EXISTS postlikes (
    like_id INTEGER PRIMARY KEY,
    from_user INTEGER,
    to_user INTEGER,
    post_id INTEGER,
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS commentlikes (
    like_id INTEGER PRIMARY KEY,
    from_user INTEGER,
    to_user INTEGER,
    post_id INTEGER,
    comment_id INTEGER,
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments(
    comment_id INTEGER PRIMARY KEY,
    content TEXT,	
    from_user INTEGER,
    to_user INTEGER,
    post_id INTEGER,
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS postshare(
    share_id INTEGER PRIMARY KEY,
    post_id INTEGER,
    from_user INTEGER,
    to_user INTEGER,
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

