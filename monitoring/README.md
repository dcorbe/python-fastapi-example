# This is what a crash test E-Mail looks like
```
Bridge Security Solutions Backend Error Report
==================================================
Timestamp: 2025-01-13T13:59:33.431182
Error: division by zero
Type: ZeroDivisionError

Request Information:
--------------------
Method: GET
URL: http://localhost:8000/crash-test-dummy
Client: 127.0.0.1

Stack Trace:
--------------------
Traceback (most recent call last):
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/middleware/errors.py", line 165, in __call__
   await self.app(scope, receive, _send)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/middleware/cors.py", line 85, in __call__
   await self.app(scope, receive, send)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
   await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
   raise exc
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
   await app(scope, receive, sender)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/routing.py", line 715, in __call__
   await self.middleware_stack(scope, receive, send)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/routing.py", line 735, in app
   await route.handle(scope, receive, send)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/routing.py", line 288, in handle
   await self.app(scope, receive, send)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/routing.py", line 76, in app
   await wrap_app_handling_exceptions(app, request)(scope, receive, send)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
   raise exc
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
   await app(scope, receive, sender)
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/starlette/routing.py", line 73, in app
   response = await f(request)
              ^^^^^^^^^^^^^^^^
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/fastapi/routing.py", line 301, in app
   raw_response = await run_endpoint_function(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 File "/Users/dcorbe/Library/Caches/pypoetry/virtualenvs/bss-backend-W-nBisWL-py3.12/lib/python3.12/site-packages/fastapi/routing.py", line 212, in run_endpoint_function
   return await dependant.call(**values)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 File "/Users/dcorbe/bss-backend/main.py", line 74, in test_crash
   1 / 0
   ~~^~~
ZeroDivisionError: division by zero
```

