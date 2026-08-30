import json
import random
import string
import threading
import time
import urllib.request
import urllib.error
from sqlalchemy import delete
import uvicorn

# Import app to run it
from app.main import app
from app.core.db import SessionLocal
from app.models import User, Community, CommunityMember, Post, Comment

PORT = 8001
BASE_URL = f"http://127.0.0.1:{PORT}"

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")

def request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            body = resp.read().decode("utf-8")
            if body:
                try:
                    return status_code, json.loads(body)
                except Exception:
                    return status_code, body
            else:
                return status_code, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            res_body = json.loads(body)
        except Exception:
            res_body = body
        return e.code, res_body

def random_string(length=10):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

def main():
    # Start server in daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1) # wait for server to start

    # Track IDs for cleanup
    user_ids = []
    community_ids = []
    post_ids = []
    comment_ids = []

    # Generate unique names
    user_a_username = f"user_a_{random_string()}"
    user_a_email = f"user_a_{random_string()}@example.com"
    user_b_username = f"user_b_{random_string()}"
    user_b_email = f"user_b_{random_string()}@example.com"
    password = "password123"

    print("--- PREPARATION: Creating User A and User B ---")
    # Register User A
    status, res = request("/users", "POST", {"username": user_a_username, "email": user_a_email, "password": password})
    assert status == 201, f"Failed to create User A: {status} {res}"
    user_a_id = res["id"]
    user_ids.append(user_a_id)

    # Register User B
    status, res = request("/users", "POST", {"username": user_b_username, "email": user_b_email, "password": password})
    assert status == 201, f"Failed to create User B: {status} {res}"
    user_b_id = res["id"]
    user_ids.append(user_b_id)

    # Login User A
    status, res = request("/auth/login", "POST", {"username": user_a_username, "password": password})
    assert status == 200, f"Failed to login User A: {status} {res}"
    token_a = res["access_token"]

    # Login User B
    status, res = request("/auth/login", "POST", {"username": user_b_username, "password": password})
    assert status == 200, f"Failed to login User B: {status} {res}"
    token_b = res["access_token"]

    # User A creates Community A
    community_a_name = f"community_a_{random_string()}"
    status, res = request("/communities", "POST", {"name": community_a_name, "description": "Community A Desc"}, token_a)
    assert status == 201, f"Failed to create Community A: {status} {res}"
    community_a_id = res["id"]
    community_ids.append(community_a_id)

    # Verify initial database state (User A is NOT a member of Community A)
    # Check members count
    status, res = request(f"/communities/{community_a_id}/members", "GET")
    assert status == 200
    assert len(res) == 0, f"Community A should have 0 members, got {len(res)}"

    results = {}

    print("--- RUNNING MANDATORY TESTS ---")

    # TEST 1 — CREATOR WITHOUT MEMBERSHIP
    status, res = request(f"/communities/{community_a_id}/membership", "GET", token=token_a)
    results["TEST 1 — CREATOR WITHOUT MEMBERSHIP"] = (200, status, res == {"is_member": False, "is_creator": True})
    print(f"TEST 1: Status={status}, Response={res}")

    # TEST 2 — NORMAL NON-MEMBER
    status, res = request(f"/communities/{community_a_id}/membership", "GET", token=token_b)
    results["TEST 2 — NORMAL NON-MEMBER"] = (200, status, res == {"is_member": False, "is_creator": False})
    print(f"TEST 2: Status={status}, Response={res}")

    # TEST 3 — NORMAL MEMBER
    # User B joins Community A
    join_status, join_res = request(f"/communities/{community_a_id}/join", "POST", token=token_b)
    assert join_status == 201, f"Failed to join: {join_status} {join_res}"
    status, res = request(f"/communities/{community_a_id}/membership", "GET", token=token_b)
    results["TEST 3 — NORMAL MEMBER"] = (200, status, res == {"is_member": True, "is_creator": False})
    print(f"TEST 3: Status={status}, Response={res}")

    # TEST 4 — CREATOR JOINS
    # User A joins Community A
    join_status, join_res = request(f"/communities/{community_a_id}/join", "POST", token=token_a)
    assert join_status == 201, f"Failed to join: {join_status} {join_res}"
    status, res = request(f"/communities/{community_a_id}/membership", "GET", token=token_a)
    results["TEST 4 — CREATOR JOINS"] = (200, status, res == {"is_member": True, "is_creator": True})
    print(f"TEST 4: Status={status}, Response={res}")

    # TEST 5 — LEAVE
    # User B leaves Community A
    leave_status, leave_res = request(f"/communities/{community_a_id}/join", "DELETE", token=token_b)
    assert leave_status == 204
    status, res = request(f"/communities/{community_a_id}/membership", "GET", token=token_b)
    results["TEST 5 — LEAVE"] = (200, status, res == {"is_member": False, "is_creator": False})
    print(f"TEST 5: Status={status}, Response={res}")

    # TEST 6 — REJOIN
    # User B rejoins Community A
    join_status, join_res = request(f"/communities/{community_a_id}/join", "POST", token=token_b)
    assert join_status == 201
    status, res = request(f"/communities/{community_a_id}/membership", "GET", token=token_b)
    results["TEST 6 — REJOIN"] = (200, status, res == {"is_member": True, "is_creator": False})
    print(f"TEST 6: Status={status}, Response={res}")

    # TEST 7 — NONEXISTENT COMMUNITY
    status, res = request("/communities/999999/membership", "GET", token=token_b)
    results["TEST 7 — NONEXISTENT COMMUNITY"] = (404, status, status == 404)
    print(f"TEST 7: Status={status}, Response={res}")

    # TEST 8 — UNAUTHENTICATED
    status, res = request(f"/communities/{community_a_id}/membership", "GET")
    results["TEST 8 — UNAUTHENTICATED"] = (401, status, status == 401)
    print(f"TEST 8: Status={status}, Response={res}")

    # TEST 9 — OTHER COMMUNITY
    # Create Community B by User A
    community_b_name = f"community_b_{random_string()}"
    status_cb, res_cb = request("/communities", "POST", {"name": community_b_name, "description": "Community B Desc"}, token_a)
    assert status_cb == 201
    community_b_id = res_cb["id"]
    community_ids.append(community_b_id)
    
    # User B is a member of Community A but not Community B.
    status, res = request(f"/communities/{community_b_id}/membership", "GET", token=token_b)
    results["TEST 9 — OTHER COMMUNITY"] = (200, status, res == {"is_member": False, "is_creator": False})
    print(f"TEST 9: Status={status}, Response={res}")

    # TEST 10 — RESPONSE SAFETY
    status, res = request(f"/communities/{community_a_id}/membership", "GET", token=token_b)
    assert status == 200
    safe = set(res.keys()) == {"is_member", "is_creator"}
    safe = safe and isinstance(res["is_member"], bool) and isinstance(res["is_creator"], bool)
    results["TEST 10 — RESPONSE SAFETY"] = (200, status, safe)
    print(f"TEST 10: Status={status}, Response={res}, Safe={safe}")

    print("--- RUNNING REGRESSION TESTS ---")

    # 1. Auth regression
    status_reg, res_reg = request("/users/me", "GET", token=token_b)
    assert status_reg == 200 and res_reg["username"] == user_b_username, "GET /users/me failed"

    # 2. Communities regression
    status_reg, res_reg = request("/communities", "GET")
    assert status_reg == 200 and len(res_reg) >= 2, "GET /communities failed"
    status_reg, res_reg = request(f"/communities/{community_a_id}", "GET")
    assert status_reg == 200 and res_reg["name"] == community_a_name, "GET /communities/{id} failed"

    # 3. Membership regression
    status_reg, res_reg = request(f"/communities/{community_a_id}/members", "GET")
    assert status_reg == 200 and any(m["username"] == user_b_username for m in res_reg), "GET /communities/{id}/members failed"

    # 4. Posts regression
    user_c_username = f"user_c_{random_string()}"
    user_c_email = f"user_c_{random_string()}@example.com"
    status_c, res_c = request("/users", "POST", {"username": user_c_username, "email": user_c_email, "password": password})
    assert status_c == 201
    user_ids.append(res_c["id"])
    status_c_login, res_c_login = request("/auth/login", "POST", {"username": user_c_username, "password": password})
    assert status_c_login == 200
    token_c = res_c_login["access_token"]
    
    status_post_auth, res_post_auth = request(f"/communities/{community_a_id}/posts", "POST", {"title": "Title", "content": "Content"}, token_c)
    assert status_post_auth == 403, f"Non-member should get 403 when posting, got {status_post_auth} {res_post_auth}"
    
    status_post_reg, res_post_reg = request(f"/communities/{community_a_id}/posts", "POST", {"title": "B Post", "content": "B Content"}, token_b)
    assert status_post_reg == 201, f"Member should get 201 when posting, got {status_post_reg} {res_post_reg}"
    post_id = res_post_reg["id"]
    post_ids.append(post_id)

    status_reg, res_reg = request(f"/communities/{community_a_id}/posts", "GET")
    assert status_reg == 200 and len(res_reg) >= 1, "GET /communities/{id}/posts failed"

    status_reg, res_reg = request(f"/posts/{post_id}", "GET")
    assert status_reg == 200 and res_reg["title"] == "B Post", "GET /posts/{id} failed"

    status_reg, res_reg = request(f"/posts/{post_id}", "PATCH", {"title": "B Post Updated"}, token_b)
    assert status_reg == 200 and res_reg["title"] == "B Post Updated", "PATCH /posts/{id} failed"

    # 5. Comments regression
    status_reg, res_reg = request(f"/posts/{post_id}/comments", "POST", {"content": "Great post!"}, token_a)
    assert status_reg == 201
    comment_id = res_reg["id"]
    comment_ids.append(comment_id)

    status_reg, res_reg = request(f"/posts/{post_id}/comments", "GET")
    assert status_reg == 200 and len(res_reg) >= 1, "GET /posts/{id}/comments failed"

    status_reg, res_reg = request(f"/comments/{comment_id}", "GET")
    assert status_reg == 200 and res_reg["content"] == "Great post!", "GET /comments/{id} failed"

    status_reg, res_reg = request(f"/comments/{comment_id}", "PATCH", {"content": "Awesome post!"}, token_a)
    assert status_reg == 200 and res_reg["content"] == "Awesome post!", "PATCH /comments/{id} failed"

    status_reg, res_reg = request(f"/comments/{comment_id}", "DELETE", token=token_a)
    assert status_reg == 204, "DELETE /comments/{id} failed"
    comment_ids.remove(comment_id)

    status_reg, res_reg = request(f"/posts/{post_id}", "DELETE", token=token_b)
    assert status_reg == 204, "DELETE /posts/{id} failed"
    post_ids.remove(post_id)

    # 6. Health / docs regression
    status_reg, res_reg = request("/health", "GET")
    assert status_reg == 200 and res_reg == {"status": "ok"}, "GET /health failed"

    status_reg, res_reg = request("/health/db", "GET")
    assert status_reg == 200 and res_reg == {"status": "ok", "database": "connected"}, "GET /health/db failed"

    status_reg, res_reg = request("/docs", "GET")
    assert status_reg == 200, "GET /docs failed"

    status_reg, res_reg = request("/openapi.json", "GET")
    assert status_reg == 200, "GET /openapi.json failed"

    print("--- ALL REGRESSION TESTS PASSED ---")

    print("--- DB CLEANUP ---")
    with SessionLocal() as session:
        if comment_ids:
            session.execute(delete(Comment).where(Comment.id.in_(comment_ids)))
        if post_ids:
            session.execute(delete(Post).where(Post.id.in_(post_ids)))
        if community_ids:
            session.execute(delete(CommunityMember).where(CommunityMember.community_id.in_(community_ids)))
            session.execute(delete(Community).where(Community.id.in_(community_ids)))
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()
    print("Cleanup successful.")

    print("--- TEST SUMMARY ---")
    all_passed = True
    for test_name, (expected_status, actual_status, condition_met) in results.items():
        pass_fail = "PASS" if condition_met else "FAIL"
        if not condition_met:
            all_passed = False
        print(f"{test_name} | Expected Status: {expected_status} | Actual Status: {actual_status} | {pass_fail}")

    if all_passed:
        print("ALL TESTS PASSED SUCCESSFULLY.")
    else:
        print("SOME TESTS FAILED.")
        exit(1)

if __name__ == "__main__":
    main()
