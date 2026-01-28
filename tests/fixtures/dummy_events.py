
# Generic Events
class MyEmitter:
    def do_thing(self):
        # Federation Lane
        self.bus.publish("user.created", {"id": 123})
        # Local Lane
        self.emit(event="internal_signal")
        # Variable (Low Confidence)
        my_event = "dynamic_" + str(1)
        self.dispatch(my_event)
        
# Crown Bus
class SeraphinaCore:
    def signal(self):
        # Crown Lane
        self.bus.publish("crown://seraphina/core/emotion/state", {"state": "joy"})

