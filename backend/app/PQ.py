import heapq
import itertools
import string

class Ticket: 
    def __init__(self, priorityGiven: string, user: string, desc: string, estimatedPriority:int):
        self.estimatedPriority = estimatedPriority
        self.user = user
        self.desc = desc
        self.priorityGiven = priorityGiven

    def __repr__(self):
        return f"(priorityGiven={self.priorityGiven}, {self.user})"


class TicketQueue:
    def __init__(self):
        self.heap = []
        self.counter = itertools.count()

    def insert(self, ticket):
        #tuple
        heapq.heappush(self.heap, (-ticket.estimatedPriority, next(self.counter), ticket))

    def remove_max(self):
        if self.heap:
            return heapq.heappop(self.heap)[2]
        return None

# so we going to have the estimated be stored as a number
# but the given will be a string, that way 
