

def run_step(task, current_step):
    task.steps[current_step](1, 2, 3, name='John', details = {'age': 20, 'is_smoker': False})
