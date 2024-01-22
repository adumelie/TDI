python3 graph.py ../../Experiment/USERS/1/Logs/*.datalog 0
python3 graph.py ../../Experiment/USERS/2/Logs/2023-12-15_15:20:02.402547.datalog 0
python3 graph.py ../../Experiment/USERS/2/Logs/2023-12-15_15:26:28.473169.datalog 0
python3 graph.py ../../Experiment/USERS/3/Logs/*.datalog 0
python3 graph.py ../../Experiment/USERS/4/Logs/*.datalog 0
python3 graph.py ../../Experiment/USERS/5/Logs/*.datalog 0
python3 graph.py ../../Experiment/USERS/6/Logs/*.datalog 0

mkdir -p ../../Experiment/Graphs
cp ../../Experiment/USERS/1/Logs/*.png ../../Experiment/Graphs/User1.png
cp ../../Experiment/USERS/2/Logs/2023-12-15_15:20:02.402547.datalog-User2-Data.png  ../../Experiment/Graphs/User2Part1.png 
cp ../../Experiment/USERS/2/Logs/2023-12-15_15:26:28.473169.datalog-User2-Data.png ../../Experiment/Graphs/User2Part2.png 
cp ../../Experiment/USERS/3/Logs/*.png ../../Experiment/Graphs/User3.png
cp ../../Experiment/USERS/4/Logs/*.png ../../Experiment/Graphs/User4.png
cp ../../Experiment/USERS/5/Logs/*.png ../../Experiment/Graphs/User5.png
cp ../../Experiment/USERS/6/Logs/*.png ../../Experiment/Graphs/User6.png
