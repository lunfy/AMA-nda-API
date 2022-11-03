CREATE_USER= (
    "INSERT INTO users (uid,email) VALUES (%s,%s) RETURNING uid, email"
)

SELECT_USERS= (
    "SELECT * FROM users"
)

FIND_USER= (
    "SELECT uid FROM users WHERE uid = (%s)"
)

UPDATE_SIGNIN= (
    "UPDATE users SET lastlogin = CURRENT_TIME, logincount = logincount+1 WHERE uid = (%s) RETURNING lastlogin"
)

FIND_USER_REQUESTS= (
    "SELECT * FROM requests WHERE user_id = (%s)"
)

INSERT_REQUEST= (
    "INSERT INTO requests (user_id, user_request, ai_response) VALUES (%s,%s,%s) RETURNING request_id"
)

FIND_USER_NOTIFICATIONS= (
    "SELECT * FROM notifications WHERE sent_to = (%s)"
)

SEND_NOTIFICATIONS= (
    "INSERT INTO notifications (generated_by, message, sent_to) VALUES (%s,%s,%s)"
)

UPDATE_NOTE_VIS= (
    "UPDATE notifications SET visible = (%s) WHERE notification_id = (%s)"
)

DELETE_NOTE= (
    "DELETE FROM notifications WHERE notification_id = (%s)"
)

CHECK_ADMIN= (
    "SELECT admin_id FROM administrators WHERE user_id = (%s)"
)