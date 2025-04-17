import threading

""" Implementation of main AX25 Timers T1 and T3 """
class Timers:

    def __init__(self, transceiver, timer_reset_t1, timer_cancel_t1, timer_reset_t3, timer_cancel_t3, timer_t1_seconds=2, timer_t3_seconds=5):
        self.transceiver = transceiver
        self.timer_t1_seconds = timer_t1_seconds
        self.timer_t3_seconds = timer_t3_seconds
        self._thread = threading.Thread(target=self._run, name="Timer control thread")
        self._kill = threading.Event()
        self.timer_reset_t1 = timer_reset_t1
        self.timer_cancel_t1 = timer_cancel_t1
        self.timer_reset_t3 = timer_reset_t3
        self.timer_cancel_t3 = timer_cancel_t3
        self._kill = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:

        """
        Starts the timer thread. If the thread is already running, this
        does nothing. If the thread is not yet running, this starts it.
        """
        try:
            with self._lock:
                if not self._thread.is_alive():
                    self._thread.start()
                if not self._running.is_set():
                    self._running.set()
        except:
            self.transceiver.logger.debug("Something went wrong")


    """ Thread loop that manages the timers T1 and T3 """
    def _run(self):

        self.local_timer_t1 = None
        self.local_timer_t3 = None
    
        while not self._kill.is_set():
            if self.timer_reset_t1.wait(timeout=0.01) or self.timer_reset_t3.wait(timeout=0.01): # Wait for any of the timers to reset, check for kill every 10ms
                if self.timer_reset_t1.is_set(): #T1 timer reset
                    if self.local_timer_t1:
                        self.local_timer_t1.cancel()
                    self.local_timer_t1 = threading.Timer(self.timer_t1_seconds, self.t1_timeout_handler)
                    self.local_timer_t1.start()
                    self.timer_reset_t1.clear()
        
                if self.timer_reset_t3.is_set(): #T3 timer reset
                    if self.local_timer_t3:
                        self.local_timer_t3.cancel()
                    self.local_timer_t3 = threading.Timer(self.timer_t3_seconds, self.t3_timeout_handler)
                    self.local_timer_t3.start()
                    self.timer_reset_t3.clear()


    """ 
    Timer T1 Timeout means singular lost I frame, that is not caught by sequence error 
    Resolve by sending RR/RNR frame with P bit set to poll distant TNC

    """
    def t1_timeout_handler(self):
        
        self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com":'COM'})
        self.local_timer_t1 = threading.Timer(self.timer_t1_seconds, self.t1_timeout_handler)
        self.local_timer_t1.start()
        return


    """
    Timer T3 is used when no I frames are outstanding and T1 is not running.
    To check on link integrity, T3 timeout causes a RR/RNR frame poll.
    """
    def t3_timeout_handler(self):
        pass