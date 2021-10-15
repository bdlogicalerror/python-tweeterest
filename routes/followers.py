import secrets

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/followers', methods=['GET'])
def actionFollowers():
    conn = mariadb.connect(
        user=dbcreds.user,
        password=dbcreds.password,
        host=dbcreds.host,
        port=dbcreds.port,
        database=dbcreds.database
    )
    cursor = conn.cursor()
    if xApiToken().checkHasToken():
        if request.method == 'GET':
            data = request.json
            if "userId" in data:
                userID = data.get("userId")

                cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [userID])
                check_id_valid = cursor.fetchone()[0]

                if check_id_valid == 1:
                    cursor.execute("SELECT id, email, username, bio, birthdate, imageurl, bannerurl \
                                                        FROM user u INNER JOIN follow f ON u.id = f.follower WHERE f.followed=?",
                                   [userID])

                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))

                    return jsonify(json_data), 200
                else:
                    return jsonify({
                        'message': "user  not found"
                    }), 404
            else:
                return jsonify({
                    'message': "user id not found"
                }), 400

    else:
        return Response("X-Api-Key not found", mimetype='application/json', status=400)
