CREATE TABLE IF NOT EXISTS conversation_history (
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL UNIQUE,
  messages TEXT NOT NULL DEFAULT '[]'
);
