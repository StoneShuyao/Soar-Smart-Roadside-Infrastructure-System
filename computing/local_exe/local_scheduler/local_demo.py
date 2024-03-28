import os
import time
import random
import logging
import argparse
import yaml

from enum import Enum
from operator import attrgetter
from typing import NamedTuple


time_safe_scalar = 1.2

parser = argparse.ArgumentParser()
parser.add_argument('--node_id', type=int, default=9)
parser.add_argument('--model_variance', type=bool, default=True, action=argparse.BooleanOptionalAction)
parser.add_argument('--max_sim_time', type=int, default=1000)
args = parser.parse_args()

nodeid = args.node_id
node_config = f"./node/node{nodeid:d}_config.yml"
method = 'soar' if args.model_variance is True else 'baseline'


log_name = f"node{nodeid:d}_{method:s}_output.log"
logging.basicConfig(
    filename=log_name,
    filemode="w",
    format='[%(asctime)s] [%(levelname)7s]: %(message)s',
    level=logging.DEBUG
)


class ModelSize(Enum):
    Full = 0
    Small = 1


class TaskData(NamedTuple):
    name: str
    create_time: float
    deadline: float
    running_time: dict[ModelSize, float]

    def __str__(self):
        return f"dataID={self.name:12s}, ddl={self.deadline:5.0f}"

    @property
    def most_urgent_time(self):
        return self.deadline


class Task:
    def __init__(self) -> None:
        self.name = ''
        self._data_queue: list[TaskData] = list()  # data queue of the whole simulation
        self.current_time: float = 0

    @property
    def data_queue(self) -> list[TaskData]:  # get the data queue until now (filter out data didn't created)
        return [d for d in self._data_queue if d.create_time <= self.current_time]

    def set_time(self, t: float) -> None:
        self.current_time = t

    def run(self, size: ModelSize = ModelSize.Full) -> TaskData:
        assert self.front is not None
        time.sleep(1e-3 * self.front.running_time[size])
        return self._data_queue.pop(0)

    def skip(self) -> TaskData:
        return self._data_queue.pop(0)

    @property
    def most_urgent_time(self) -> float:
        if len(self.data_queue) == 0:
            return float('+inf')
        else:
            return min(d.most_urgent_time for d in self.data_queue)

    @property
    def front(self) -> TaskData | None:
        if len(self._data_queue) == 0:
            return None
        else:
            return self._data_queue[0]

    @property
    def keep_simulation(self) -> bool:
        return len(self._data_queue) > 0

    def __str__(self) -> str:
        return f"{self.name}"


if __name__ == '__main__':
    try:
        with open(node_config) as f:
            configs = yaml.safe_load(f)
    except Exception as err:
        logging.error(err)
        exit(-1)

    tasks: list[Task] = []
    for config in configs:
        task_name, task_config = next(iter(config.items()))
        task = Task()
        task.name = task_name
        for create_time in range(task_config['start_shift'], args.max_sim_time, task_config['period']):
            task._data_queue.append(TaskData(
                name=task_name + str(create_time),
                create_time=create_time + random.random() * 2 - 1,
                deadline=create_time + task_config['deadline'],
                running_time={
                    ModelSize.Small: task_config['exec_time']['small'],
                    ModelSize.Full: task_config['exec_time']['full']
                }
            ))
        tasks.append(task)

    data_success, data_skip, data_fail = 0, 0, 0
    print(f"{method:s}: node {nodeid} is started.")

    start_time = time.time()
    while any(task.keep_simulation for task in tasks):
        # update the simulation time
        current_time = (time.time() - start_time) * 1e3
        for task in tasks:
            task.set_time(current_time)

        # get the top-1 & top-2 urgent task
        current_task, next_task, *_ = sorted(tasks, key=attrgetter('most_urgent_time'))
        current_task: Task
        next_task: Task

        # in case no task has data, spinning waiting
        if current_task.most_urgent_time == float('+inf'):
            # logging.info(f"waiting for data")
            continue

        if args.model_variance:
            # soar
            current_data = current_task.front
            current_deadline = current_data.deadline

            next_data = next_task.front
            # in case the second data of current task is most urgent
            if len(current_task.data_queue) >= 2 and \
                    (next_data is None or next_data.most_urgent_time > current_task.data_queue[1].most_urgent_time):
                next_data = current_task.data_queue[1]
            next_deadline = None if next_data is None else next_data.deadline

            if current_time + current_data.running_time[ModelSize.Small] * time_safe_scalar > current_deadline:  # cannot finish on time anyway
                skipped_data: TaskData = current_task.skip()
                logging.warning(f"skipped data ({skipped_data})")
                data_skip += 1
                continue
            elif current_time + current_data.running_time[ModelSize.Full] * time_safe_scalar > current_deadline:  # small can finish, while full cannot
                model_size: ModelSize = ModelSize.Small
            else:
                if next_deadline is not None and current_time + current_data.running_time[ModelSize.Full] * time_safe_scalar + next_data.running_time[ModelSize.Small] * time_safe_scalar > next_deadline:
                    model_size: ModelSize = ModelSize.Small
                else:
                    model_size: ModelSize = ModelSize.Full
        else:
            # baseline
            model_size: ModelSize = ModelSize.Full

        running_info = f"running task {str(current_task):15s}, with data ({str(current_task.front):15s}), model_size: {str(model_size):15s}"
        logging.info(f"start " + running_info)
        ran_data: TaskData = current_task.run(model_size)

        current_time = (time.time() - start_time) * 1e3
        if current_time > ran_data.deadline:
            data_fail += 1
            logging.warning(f"  end " + running_info + f", <TIMEOUT> for {current_time - ran_data.deadline:5.1f}ms")
        else:
            logging.info(f"  end " + running_info + f", on time ({ran_data.deadline - current_time:5.1f}ms before ddl)")
            data_success += 1
    total_data = sum((data_success, data_skip, data_fail))
    logging.info(f"successful jobs: {data_success} ({data_success / total_data:5.1%}), skip jobs: {data_skip} ({data_skip / total_data:5.1%}), failed jobs: {data_fail} ({data_fail / total_data:5.1%})")
    print(f"{method:s}: node {nodeid} is terminated, log at {os.getcwd() + '/' + log_name:s}")
