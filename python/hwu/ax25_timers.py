import threading

""" Implementation of main AX25 Timers T1 and T3 """
class Timers:

    def __init__(self, transceiver, timer_reset_t1, timer_reset_t3, timer_t1_seconds=2, timer_t3_seconds=5):
        self.transceiver = transceiver
        self.timer_t1_seconds = timer_t1_seconds
        self.timer_t3_seconds = timer_t3_seconds
        self._thread = threading.Thread(target=self._run, name="Timer control thread")
        self._kill = threading.Event()
        self.timer_reset_t1 = timer_reset_t1
        self.timer_reset_t3 = timer_reset_t3
        self._kill = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:

        try:
            with self._lock:
                if not self._thread.is_alive():
                    self._thread.start()
                if not self._running.is_set():
                    self._running.set()
        except:
            self.transceiver.logger.debug("Something went wrong")


    def _run(self):
        while not self._kill.is_set():
            if self.timer_reset_t1.is_set():
                try:
                    local_timer_t1.cancel()
                except:
                    pass
                local_timer_t1 = threading.Timer(self.timer_t1_seconds, self.t1_timeout_handler)
                local_timer_t1.start()
            if self.timer_reset_t3.is_set():
                try:
                    local_timer_t3.cancel()
                except:
                    pass
                local_timer_t3 = threading.Timer(self.timer_t3_seconds, self.t3_timeout_handler)
                local_timer_t3.start()

        return




    def t1_timeout_handler(self):
        pass

    def t3_timeout_handler(self):
        pass