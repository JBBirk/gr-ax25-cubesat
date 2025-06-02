import threading

""" Implementation of main AX25 Timers T1 and T3 """
class Timers:

    def __init__(self, transceiver, timer_reset_t1, timer_cancel_t1, timer_reset_t3, timer_cancel_t3, timer_t1_seconds=2, timer_t3_seconds=5):
        self.transceiver = transceiver
        self.timer_t1_seconds = timer_t1_seconds
        self.timer_t3_seconds = timer_t3_seconds
        self._thread = threading.Thread(target=self._run, name="Timer control thread", daemon=True)
        self._kill = threading.Event()
        self._running = threading.Event()
        self.events = {"reset_t1":timer_reset_t1,
                       "cancel_t1": timer_cancel_t1,
                       "reset_t3": timer_reset_t3,
                       "cancel_t3": timer_cancel_t3}
        self.handlers = {"t1": self.t1_timeout_handler,
                         "t3": self.t3_timeout_handler}
        self.timers = {}
        self._kill = threading.Event()
        self._lock = threading.Lock()
        # self.timer_active_t1 = False
        # self.timer_active_t3 = False

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
        except Exception as e:
            self.transceiver.logger.debug(f"Timers thread could not be started due to: {e}")

    
    """ Thread loop that starts timers T1 and T3, then idles """
    def _run(self):

        self.transceiver.logger.debug("Setting up daughter threads")
        self.setup_event_threads()

        self.transceiver.logger.debug("Entering run loop")
        while not self._kill.is_set():
            self._kill.wait(timeout=1)


        
        # self.local_timer_t1 = None
        # self.local_timer_t3 = None

        # self.setup_timers()

        # # for event in [self.timer_cancel_t1, self.timer_reset_t1, self.timer_cancel_t3, self.timer_reset_t3]:
        # threading.Thread(target=self.wait_for_event, args=[self.timer_cancel_t1, ], daemon=True).start()
    
        # while not self._kill.is_set():
        #     if self.timer_reset_t1.wait(timeout=0.1) or self.timer_reset_t3.wait(timeout=0.1) or self.timer_cancel_t1.wait(timeout=0.1) or self.timer_cancel_t3.wait(timeout=0.1): # Wait for any of the timers to reset, check for kill every 100ms

        #         if self.timer_reset_t1.is_set(): #T1 timer reset
        #             if self.local_timer_t1:
        #                 self.local_timer_t1.cancel()
        #             self.local_timer_t1 = threading.Timer(self.timer_t1_seconds, self.t1_timeout_handler)
        #             self.local_timer_t1.start()
        #             self.timer_active_t1 = True
        #             self.timer_reset_t1.clear()
        
        #         if self.timer_reset_t3.is_set(): #T3 timer reset
        #             if self.local_timer_t3:
        #                 self.local_timer_t3.cancel()
        #             self.local_timer_t3 = threading.Timer(self.timer_t3_seconds, self.t3_timeout_handler)
        #             self.local_timer_t3.start()
        #             self.timer_active_t3 = True
        #             self.timer_reset_t3.clear()


    """ 
    Timer T1 Timeout means singular lost I frame, that is not caught by sequence error 
    Resolve by sending RR/RNR frame with P bit set to poll distant TNC 
    """
    def t1_timeout_handler(self): #TODO Work on respnoses to this Poll
        
        # with self.transceiver.lock:
        # if self.transceiver.t1_try_count == self.transceiver.retries:
        if self.transceiver.get_t1_try_count() == self.transceiver.retries:
            self.transceiver.logger.warning("Maximum T1 retries reached, something has gone seriously wrong!") #TODO 
            return
        
        self.transceiver.logger.debug("T1 Timeout")
        with self.transceiver.lock:
            self.transceiver.framequeue.insert(0,
                                                {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid],
                                                "Type":'RNR' if self.transceiver.state == 'BUSY' else 'RR',
                                                "Poll":True, 
                                                "Payload": None, 
                                                "Com":'COM'})
        self.transceiver.set_t1_try_count(self.transceiver.get_t1_try_count() + 1) #TODO Check if this is correct
        
        self.reset_timer("t1")

        return


    """
    Timer T3 is used when no I frames are outstanding and T1 is not running.
    To check on link integrity, T3 timeout causes a RR/RNR frame poll.
    """
    def t3_timeout_handler(self):
        pass


    def setup_event_threads(self):

        self.transceiver.logger.debug("Inside thread setup function")
        for name, event in self.events.items():
            threading.Thread(target=self.wait_for_event,
            args=[event, 
            "t1" if name[-2:] == "t1" else "t3", #select appropriate timer
            self.reset_timer if name[:-3] == "reset" else self.cancel_timer], #se;ect appropriate handler (reset or cancel)
            daemon=True,
            name=f"WaitFor{name}").start()
            self.transceiver.logger.debug(f"Started thread to wait for {name}, event: {event}")


    def cancel_timer(self, timer_name):
        if timer_name in self.timers:
            self.timers[timer_name].cancel()


    def reset_timer(self, timer_name):
        self.transceiver.logger.debug(f"(Re)setting timer {timer_name}")
        if timer_name in self.timers:
            self.timers[timer_name].cancel() #Cancel timer, if it exists
        self.timers[timer_name] = threading.Timer(self.timer_t1_seconds if timer_name[-2:] == "t1" else self.timer_t3_seconds, 
                                                  self.handlers[timer_name], 
                                                  args=[]) 
        self.timers[timer_name].start()
        

    def wait_for_event(self, event:threading.Event, timer_name:str, response_function) -> None: #TODO: Check if this is the way
        while True:
            event.wait()
            response_function(timer_name)
            event.clear()


