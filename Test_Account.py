import pytest
from fastapi.testclient import TestClient
from main import app
from Config import author_collection, blog_collection, author_blog_collection
from pymongo import MongoClient

client = TestClient(app)

# Helper to clear collections before each test
@pytest.fixture(autouse=True)
def clear_collections():
    author_collection.delete_many({})
    blog_collection.delete_many({})
    author_blog_collection.delete_many({})

# Test user creation
def test_create_user():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    response = client.post("/Author/", json=user_data)
    assert response.status_code == 201
    assert response.json() == {"message": "Signed up successfully"}

# Test user creation with already registered username
def test_create_user_already_registered():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    response = client.post("/Author/", json=user_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

# Test login for access token
def test_login_for_access_token():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

# Test login failed with incorrect credentials
def test_login_failed():
    response = client.post("/token", data={"username": "testuser", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

# Test delete user
def test_delete_user():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    token_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = token_response.json()["access_token"]
    response = client.delete("/Author/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted successfully"}

# Test update user
def test_update_user():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    token_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = token_response.json()["access_token"]
    update_data = {"password": "newpassword"}
    response = client.patch("/Author/me", json=update_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "User updated successfully"}

# Test get current user
def test_get_current_user():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    token_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = token_response.json()["access_token"]
    response = client.get("/Author/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"username": "testuser","password": "testpassword", "age": 30}

# Test get all authors
def test_get_all_authors():
    user_data1 = {"username": "testuser1", "password": "testpassword1", "age": 25}
    user_data2 = {"username": "testuser2", "password": "testpassword2", "age": 35}
    client.post("/Author/", json=user_data1)
    client.post("/Author/", json=user_data2)
    response = client.get("/authors/")
    assert response.status_code == 200
    authors = response.json()
    assert len(authors) == 2
    assert any(author["username"] == "testuser1" for author in authors)
    assert any(author["username"] == "testuser2" for author in authors)
