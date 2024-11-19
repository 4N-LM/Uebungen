class QueueError(IndexError):  # Choose base class for the new exception.
    pass


class Queue:
    def __init__(self):
        self.__queue_list = []

    def put(self, elem):
        self.__queue_list.append(elem)

    def get(self):
        if len(self.__queue_list) > 0:
            tmp = self.__queue_list[0]
            del self.__queue_list[0]
            return tmp
        else:
            raise QueueError
        
        


que = Queue()
que.put(1)
que.put("dog")
que.put(False)
try:
    for i in range(4):
        print(que.get())
except:
    print("Queue error")
