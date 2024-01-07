# Start a code application for code
# uvicorn  main:app --reload --host 0.0.0.0 &
gunicorn main:app -w 3 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker --threads 1
