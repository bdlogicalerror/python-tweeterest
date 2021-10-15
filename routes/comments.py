from datetime import datetime

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/comments', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def commentAction():
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

            if len(data.keys()) == 1 and "tweetId" in data:
                cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [data['tweetId']])
                checkTweet = cursor.fetchone()[0]

                if checkTweet == 1:
                    cursor.execute(
                        "SELECT com.id as commentId,com.created_at, com.tweet_id as tweetId,com.content,u.username, "
                        "u.id as userId FROM comment com INNER "
                        "JOIN user u ON "
                        "com.user_id = "
                        "u.id "
                        "where com.tweet_id=?", [data['tweetId']])
                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))

                    return jsonify(json_data), 200
                else:
                    return jsonify({
                        "message": "tweet not found"
                    }), 404
            else:
                return jsonify({
                    "message": "Invalid requests"
                }), 200
        elif request.method == "POST":
            data = request.json

            if len(data.keys()) == 3 and {"loginToken", "tweetId", "content"} <= data.keys():
                tweet_id = data.get("tweetId")
                token = data.get("loginToken")

                if token is not None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                        userId = cursor.fetchone()[0]

                        cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [tweet_id])
                        checkTweet = cursor.fetchone()[0]

                        if checkTweet == 1:

                            created_date = datetime.now()
                            cursor.execute("INSERT INTO comment(user_id,tweet_id,content,created_at) VALUES(?,?,?,?)",
                                           [userId, tweet_id, data['content'], created_date])
                            conn.commit()
                            lastId = cursor.lastrowid

                            cursor.execute(
                                "SELECT com.id as commentId,com.created_at, com.tweet_id as tweetId,com.content,"
                                "u.username, "
                                "u.id as userId FROM comment com INNER "
                                "JOIN user u ON "
                                "com.user_id = "
                                "u.id "
                                "where com.id=?", [lastId])
                            row_headers = [x[0] for x in cursor.description]
                            rv = cursor.fetchall()
                            json_data = []
                            for result in rv:
                                json_data.append(dict(zip(row_headers, result)))

                            return jsonify(json_data), 201

                        else:
                            return jsonify({
                                "message": "tweet not found"
                            }), 404
                    else:
                        return jsonify({
                            "message": "token invalid"
                        }), 403
                else:
                    return jsonify({
                        "message": "loginToken Required"
                    }), 400
            else:
                return jsonify({
                    "message": "invalid request params"
                }), 400
        elif request.method == "PATCH":
            data = request.json

            if len(data.keys()) == 3 and {"loginToken", "commentId", "content"} <= data.keys():
                commentId = data.get("commentId")
                token = data.get("loginToken")

                if token is not None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                        userId = cursor.fetchone()[0]

                        cursor.execute("SELECT EXISTS(SELECT id from comment WHERE id=? and user_id=?)",
                                       [commentId, userId])
                        checkComment = cursor.fetchone()[0]

                        if checkComment == 1:
                            cursor.execute("UPDATE comment SET content=? where id=?",
                                           [data['content'], commentId])
                            conn.commit()

                            cursor.execute(
                                "SELECT com.id as commentId,com.created_at, com.tweet_id as tweetId,com.content,"
                                "u.username, "
                                "u.id as userId FROM comment com INNER "
                                "JOIN user u ON "
                                "com.user_id = "
                                "u.id "
                                "where com.id=?", [commentId])
                            row_headers = [x[0] for x in cursor.description]
                            rv = cursor.fetchall()
                            json_data = []
                            for result in rv:
                                json_data.append(dict(zip(row_headers, result)))

                            return jsonify(json_data), 201

                        else:
                            return jsonify({
                                "message": "comment not found"
                            }), 404
                    else:
                        return jsonify({
                            "message": "token invalid"
                        }), 403
                else:
                    return jsonify({
                        "message": "loginToken Required"
                    }), 400
            else:
                return jsonify({
                    "message": "invalid request params"
                }), 400
        elif request.method == "DELETE":
            data = request.json

            if len(data.keys()) == 2 and {"loginToken", "commentId"} <= data.keys():
                commentId = data.get("commentId")
                token = data.get("loginToken")

                if token is not None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                        userId = cursor.fetchone()[0]

                        cursor.execute("SELECT EXISTS(SELECT id from comment WHERE id=? and user_id=?)",
                                       [commentId, userId])
                        checkComment = cursor.fetchone()[0]

                        if checkComment == 1:
                            cursor.execute("DELETE FROM comment where user_id=? and id=?",
                                           [userId, commentId])

                            conn.commit()
                            return jsonify({}), 204

                        else:
                            return jsonify({
                                "message": "tweet not found"
                            }), 404
                    else:
                        return jsonify({
                            "message": "token invalid"
                        }), 403
                else:
                    return jsonify({
                        "message": "loginToken Required"
                    }), 400
            else:
                return jsonify({
                    "message": "invalid request params"
                }), 400
    else:
        return Response("X-Api-Key not found", mimetype='application/json', status=400)