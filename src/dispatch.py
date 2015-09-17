from mpi4py import MPI

def enum(*sequential, **named):
    """Handy way to fake an enumerated type in Python
    http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

# Define MPI message MPI_TAGS
MPI_TAGS = enum('READY', 'DONE', 'EXIT', 'START')

# Initializations and preliminaries
MPI_COMM_WORLD = MPI.COMM_WORLD   # get MPI communicator object
MPI_SIZE = MPI_COMM_WORLD.size        # total number of processes
MPI_RANK = MPI_COMM_WORLD.rank        # MPI_RANK of this process
MPI_STATUS = MPI.Status()   # get MPI MPI_STATUS object

def async_tasks(tasks):
    if MPI_RANK == 0:
        # Master process executes code below
        task_index = 0
        num_workers = MPI_SIZE - 1
        closed_workers = 0
        len_tasks = len(tasks)
        results = [None] * len_tasks
        results_index = 0
        while closed_workers < num_workers:
            data = MPI_COMM_WORLD.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=MPI_STATUS)
            source = MPI_STATUS.Get_source()
            tag = MPI_STATUS.Get_tag()
            if tag == MPI_TAGS.READY:
                # Worker is ready, so send it a task
                if task_index < len_tasks:
                    MPI_COMM_WORLD.send(tasks[task_index], dest=source, tag=MPI_TAGS.START)
                    task_index += 1
                else:
                    MPI_COMM_WORLD.send(None, dest=source, tag=MPI_TAGS.EXIT)
            elif tag == MPI_TAGS.DONE:
                results[results_index] = data
                results_index += 1
            elif tag == MPI_TAGS.EXIT:
                closed_workers += 1

        return results
    else:
        # Worker processes execute code below
        # name = MPI.Get_processor_name()
        while True:
            MPI_COMM_WORLD.send(None, dest=0, tag=MPI_TAGS.READY)
            task = MPI_COMM_WORLD.recv(source=0, tag=MPI.ANY_TAG, status=MPI_STATUS)
            tag = MPI_STATUS.Get_tag()

            if tag == MPI_TAGS.START:
                # Do the work here
                result = task[0](*task[1], **task[2])
                MPI_COMM_WORLD.send(result, dest=0, tag=MPI_TAGS.DONE)
            elif tag == MPI_TAGS.EXIT:
                break

        MPI_COMM_WORLD.send(None, dest=0, tag=MPI_TAGS.EXIT)


# def square(value):
#     return value ** 2
#
# tasks = [(square, (ii,), {}) for ii in range(2000)]
#
#
# print async_tasks(tasks)