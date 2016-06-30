# this is python 3.0 webapp demo.

## install fabric
fabirc dependent on python2.7.8

## config server supervisor
touch a file -- 'awesome.conf', in '/etc/supervisor/conf.d/'
```
[program:awesome]

command     = python3 app.py
directory   = /srv/awesome/www
user        = www-data
startsecs   = 3

redirect_stderr         = true
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups  = 10
stdout_logfile          = /srv/awesome/log/app.log
```
如果直接执行，会提示“awesome: ERROR (file is not executable)”
只要修改app.py的权限，拥有执行权限即可。
```
chmod 755 /srv/awesome/www/app.py
```

## config nginx
touch 'awesome' file in '/etc/nginx/sites-available/'
```
server {
    listen      9091; # 监听9091端口

    root       /srv/awesome/www;
    access_log /srv/awesome/log/access_log;
    error_log  /srv/awesome/log/error_log;

    # server_name awesome.liaoxuefeng.com; # 配置域名

    # 处理静态文件/favicon.ico:
    location /favicon.ico {
        root /srv/awesome/www;
    }

    # 处理静态资源:
    location ~ ^\/static\/.*$ {
        root /srv/awesome/www;
    }

    # 动态请求转发到9000端口:
    location / {
        proxy_pass       http://127.0.0.1:9000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```


- 后端API包括：
    + 获取日志：GET /api/blogs
    + 创建日志：POST /api/blogs
    + 修改日志：POST /api/blogs/:blog_id
    + 删除日志：POST /api/blogs/:blog_id/delete
    + 获取评论：GET /api/comments
    + 创建评论：POST /api/blogs/:blog_id/comments
    + 删除评论：POST /api/comments/:comment_id/delete
    + 创建新用户：POST /api/users
    + 获取用户：GET /api/users

- 管理页面包括：
    + 评论列表页：GET /manage/comments
    + 日志列表页：GET /manage/blogs
    + 创建日志页：GET /manage/blogs/create
    + 修改日志页：GET /manage/blogs/
    + 用户列表页：GET /manage/users

- 用户浏览页面包括：
    + 注册页：GET /register
    + 登录页：GET /signin
    + 注销页：GET /signout
    + 首页：GET /
    + 日志详情页：GET /blog/:blog_id