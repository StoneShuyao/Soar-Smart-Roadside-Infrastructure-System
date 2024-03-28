## A Quick Demo of Local Task Scheduling

### ./node/

- Set the task config on the node (i.e., task type, data shift, deadline, execution time, etc.) according to the task dispatching results, e.g., node1_config.yml:
```
- image-yolo:
    start_shift: 1
    period: 100
    deadline: 340
    exec_time:
        full: 35
        small: 31

- pointpillar:
    start_shift: 3
    period: 50
    deadline: 510
    exec_time:
        full: 76
        small: 66
```

### local_demo.py

- Run the demo with arguments to set the node id, method, and execution time, i.e.,
```
python local_demo.py --node_id [node id] --[method] --max_sim_time [execution time]
```

- E.g., on node 1, executing 1000 ms:
```
# Soar
python local_demo.py --node_id 1 --model_variance --max_sim_time 1000

# Baseline
python local_demo.py --node_id 1 --no_model_variance --max_sim_time 1000
```