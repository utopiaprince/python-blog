# this is python 3.0 webapp demo.

- 后端API包括：
    + [x]获取日志：GET /api/blogs
    + [x]创建日志：POST /api/blogs
    + [x]修改日志：POST /api/blogs/:blog_id
    + [x]删除日志：POST /api/blogs/:blog_id/delete
    + [x]获取评论：GET /api/comments
    + [x]创建评论：POST /api/blogs/:blog_id/comments
    + [x]删除评论：POST /api/comments/:comment_id/delete
    + [x]创建新用户：POST /api/users
    + [x]获取用户：GET /api/users

- 管理页面包括：
    + [x]评论列表页：GET /manage/comments
    + [x]日志列表页：GET /manage/blogs
    + [x]创建日志页：GET /manage/blogs/create
    + [x]修改日志页：GET /manage/blogs/
    + [x]用户列表页：GET /manage/users

- 用户浏览页面包括：
    + [x]注册页：GET /register
    + [x]登录页：GET /signin
    + [x]注销页：GET /signout
    + [x]首页：GET /
    + [x]日志详情页：GET /blog/:blog_id