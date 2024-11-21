class QueueError(IndexError):  # Choose base class for the new exception.
    pass


class Queue:
    def __init__(self):
        self.queue_list = []

    def put(self, elem):
        self.queue_list.append(elem)

    def get(self):
        if len(self.queue_list) > 0:
            tmp = self.queue_list[0]
            del self.queue_list[0]
            return tmp
        else:
            raise QueueError
        
class SuperQueue(Queue):
    def is_empty(self):
        return len(self.queue_list) == 0

que = SuperQueue()
que.put(1)
que.put("dog")
que.put(False)
for i in range(4):
    if not que.is_empty():
        print(que.get())
    else:
        print("Queue empty")