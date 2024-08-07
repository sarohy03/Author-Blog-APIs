
from Config import blog_collection, author_blog_collection, author_collection
from Models import Blog
from fastapi import APIRouter, HTTPException, Depends
from .Accounts import get_current_user,User
from typing import List

router = APIRouter()


@router.post("/blogs/", response_model=Blog)
async def create_blog(blog: Blog, current_user: User = Depends(get_current_user)):

    blog_collection.insert_one(blog.dict())
    response = author_collection.find_one({'username': current_user.username})
    author_blog_collection.insert_one({'Author_id': response['_id'],'Blog_id':blog.id})
    return blog

@router.get("/blogs/", response_model=List[Blog])
async def get_blogs_of_current_user(current_user: User = Depends(get_current_user)):
    response = author_collection.find_one({'username': current_user.username})
    author_blogs = author_blog_collection.find({"Author_id": response['_id']})
    blog_ids = [entry["Blog_id"] for entry in author_blogs]
    blogs = list(blog_collection.find({"id": {"$in": blog_ids}}))
    return blogs

@router.get("/blogs/{id}", response_model=Blog)
async def get_blog_by_id_of_current_user(id: int, current_user: User = Depends(get_current_user)):
    response = author_collection.find_one({'username': current_user.username})
    author_blog = author_blog_collection.find_one({"Blog_id": id, "Author_id": response['_id']})
    if not author_blog:
        raise HTTPException(status_code=404, detail="Blog does not exist or you are not authorized to view this blog")
    blog = blog_collection.find_one({"id": id})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog does not exist")
    return blog
@router.get("/AllBlogs", response_model=List[Blog])
async def get_AllBlogs():
    blogs = list(blog_collection.find())
    return blogs