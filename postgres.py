CREATE_USER= (
    "INSERT INTO users (email) VALUES (%s) RETURNING user_id"
)

SELECT_USERS= (
    "SELECT user_id, email FROM users"
)

FIND_USER= (
    "SELECT email FROM users WHERE email = (%s)"
)

UPDATE_SIGNIN= (
    "UPDATE users SET lastlogin = CURRENT_TIME, logincount = logincount+1 WHERE email = (%s) RETURNING lastlogin"
)