from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os

from database import get_db, BlogPost

app = FastAPI(title="c0mpos3r's Blog")

# Static Files And Template Setting
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# HomePage - Show All Blog Posts 
@app.get("/", response_class=HTMLResponse)
def read_posts(request: Request, db: Session = Depends(get_db)):
    posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {
        "request" : request,
        "posts" : posts
    })

# 1 Post View
@app.get("/post/{post_id}", response_class=HTMLResponse)
def read_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    return templates.TemplateResponse("post.html", {
        "request": request, 
        "post": post
    })

# New Post Page Write
# 1. GET /create - 글 작성 폼 보여주기
@app.get("/create", response_class=HTMLResponse)
def create_post_form(request: Request):
    """새 글 작성 페이지를 보여주는 API"""
    try:
        return templates.TemplateResponse("create.html", {"request": request})
    except Exception as e:
        print(f"템플릿 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. POST /create - 실제 글 저장하기
@app.post("/create")
def create_post(
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    """새 글을 데이터베이스에 저장하는 API"""
    try:
        # 새 포스트 생성
        post = BlogPost(title=title, content=content)
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # 생성된 포스트 페이지로 리다이렉트
        return RedirectResponse(url=f"/post/{post.id}", status_code=303)
    except Exception as e:
        print(f"포스트 생성 에러: {e}")
        db.rollback()  # 에러 시 롤백
        raise HTTPException(status_code=500, detail="포스트 생성에 실패했습니다")

@app.post("/delete/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    db.delete(post)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

if __name__  == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

