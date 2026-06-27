import threading

counter = 0

def increment_counter(n: int) -> int:
    global counter
    counter = 0
    def increment():
        global counter
        for _ in range(n):
            counter += 1
    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counter
