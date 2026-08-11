cd ~/GoodLife
source .venv/bin/activate


nohup python -u -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    > goodlife.log 2>&1 &

    disown