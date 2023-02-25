import appdaemon.plugins.hass.hassapi as hass
import time

#
# Integration for pico remotes
#

class PicoRemote(hass.Hass):

  def initialize(self):
    global start_press
    global stop_press
    start_press = time.time()
    stop_press = time.time()
    self.remote_functions = self.args
    self.listen_event(self.remote_callback, "lutron_caseta_button_event")
    self.log("initialization complete, lutron pico remotes.")

  def remote_callback(self, event, data, kwargs):
    global start_press
    global stop_press
    if data["action"] == "press":
      start_press = time.time()
    else:
      stop_press = time.time()
      duration = stop_press - start_press
      default_entity = self.remote_functions[data["serial"]]
      actions = self.remote_functions["actions"]
      button_name = data['button_type']
      action = actions[button_name]
      if duration > 0.4:
        self.log("long press detected")
        if type(action) == list:
            action = action[1]
      else:
        if type(action) == list:
            action = action[0]
      service_data={"entity_id": default_entity, "action": action}
      sensitivity = duration/7
      if button_name == "raise":
        sensitivity = sensitivity
      elif button_name == "lower":
        sensitivity = -1*sensitivity
      else:
        sensitivity = 0.0
      service_data[self.remote_functions["sensitivity"]] = sensitivity
      self.call_service(self.remote_functions["service_call"], **service_data)
      
