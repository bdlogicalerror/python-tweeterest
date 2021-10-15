from datetime import datetime

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/comment-likes', methods=['GET', 'POST', 'DELETE'])
def commentLikesAction():
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

            if len(data.keys()) == 1 and "commentId" in data:
                cursor.execute("SELECT EXISTS(SELECT id from comment WHERE id=?)", [data['commentId']])
                checkTweet = cursor.fetchone()[0]

                if checkTweet == 1:
                    cursor.execute(
                        "SELECT comLike.comment_id as commentId, u.id as userId, u.username FROM comment_like comLike "
                        "INNER JOIN user u ON "
                        "comLike.user_id = u.id "
                        "where comLike.comment_id=?", [data['commentId']])
                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))

                    return jsonify(json_data), 200
                else:
                    return jsonify({
                        "message": "comment not found"
                    }), 404
            else:
                return jsonify({
                    "message": "Invalid requests"
                }), 200
        elif request.method == "POST":
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

                        cursor.execute("SELECT EXISTS(SELECT id from comment WHERE id=?)", [commentId])
                        checkComment = cursor.fetchone()[0]

                        if checkComment == 1:

                            cursor.execute(
                                "SELECT EXISTS(SELECT id from comment_like WHERE comment_id=? AND user_id=?)",
                                [commentId, userId])
                            checkCommentAlreadyLiked = cursor.fetchone()[0]
                            if checkCommentAlreadyLiked == 0:
                                created_date = datetime.now()
                                cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                                cursor.execute("INSERT INTO comment_like(user_id,comment_id, created_at) VALUES(?,?,?)",
                                               [userId, commentId, created_date])
                                cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")

                                conn.commit()
                                return jsonify({}), 201
                            else:
                                return jsonify({
                                    "message": "you already liked this comment"
                                }), 400
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

                        cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [commentId])
                        checkComment = cursor.fetchone()[0]

                        if checkComment == 1:

                            cursor.execute(
                                "SELECT EXISTS(SELECT id from comment_like WHERE comment_id=? AND user_id=?)",
                                [commentId, userId])
                            checkCommentAlreadyLiked = cursor.fetchone()[0]
                            if checkCommentAlreadyLiked == 1:
                                cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                                cursor.execute("DELETE FROM comment_like where user_id=? and comment_id=?",
                                               [userId, commentId])
                                cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")

                                conn.commit()
                                return jsonify({}), 204
                            else:
                                return jsonify({
                                    "message": "you did not liked this comment"
                                }), 400
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
    else:
        return Response("X-Api-Key not found", mimetype='application/json', status=400)
