from multiprocessing import cpu_count

bind = 'localhost:8080'
workers = cpu_count() * 2 + 1
accesslog = '-'
errorlog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Forwarded-For}i)s"'
