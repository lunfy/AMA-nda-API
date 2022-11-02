CREATE_USER= (
    "INSERT INTO users (email) VALUES (%s) RETURNING user_id"
)

SELECT_USERS= (
    "SELECT user_id, email FROM users"
)

FIND_USER= (
    "SELECT email FROM users WHERE email = (%s)"
)

FIND_USER_UID= (
    "SELECT * FROM requests WHERE user_id = (%s)"
)

UPDATE_SIGNIN= (
    "UPDATE users SET lastlogin = CURRENT_TIME, logincount = logincount+1 WHERE email = (%s) RETURNING lastlogin"
)

INSERT_REQUEST= (
    "INSERT INTO requests (user_id, user_request, ai_response) VALUES (%s,%s,%s) RETURNING request_id"
)