echo "Starting FreeEed Suite"
cd /home/ubuntu/Desktop/freeeed_complete_pack/
./start_all.sh
echo "Activating AIAdvisor Environment"
cd /home/ubuntu/projects/AIAdvisor/code/python
echo "Starting AIAdvisor API"
./run_fastapi.sh 
echo "Starting connection watcher"
python reload_on_high_connections.py &
