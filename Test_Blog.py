import pytest
from fastapi.testclient import TestClient
from main import app
from Config import author_collection, blog_collection, author_blog_collection

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_collections():
    author_collection.delete_many({})
    blog_collection.delete_many({})
    author_blog_collection.delete_many({})


def test_create_blog():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    token_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = token_response.json()["access_token"]
    blog_data = {"id": 12, "description": "Test blog description"}
    response = client.post("/blogs/", json=blog_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == blog_data

def test_get_blogs_of_current_user():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    token_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = token_response.json()["access_token"]
    blog_data = {"id": 1, "description": "Test blog description"}
    client.post("/blogs/", json=blog_data, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/blogs/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 1
    assert blogs[0]["id"] == 1

def test_get_blog_by_id_of_current_user():
    user_data = {"username": "testuser", "password": "testpassword", "age": 30}
    client.post("/Author/", json=user_data)
    token_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = token_response.json()["access_token"]
    blog_data = {"id": 1, "description": "Test blog description"}
    client.post("/blogs/", json=blog_data, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/blogs/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == blog_data

def test_get_all_blogs():
    blog_data1 = {"id": 1, "description": "Test blog description 1"}
    blog_data2 = {"id": 2, "description": "Test blog description 2"}
    blog_collection.insert_one(blog_data1)
    blog_collection.insert_one(blog_data2)
    response = client.get("/AllBlogs")
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 2
    assert any(blog["id"] == 1 for blog in blogs)
    assert any(blog["id"] == 2 for blog in blogs)
