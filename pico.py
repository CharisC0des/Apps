import appdaemon.plugins.hass.hassapi as hass
import time

#
# Integration for pico remotes
#
"""
Ensuite Play/Pause button press event:
data:
  serial: 91567021 --ensuite pico remote
  serial: 91952379 --bluesound pico remote
  button_type: "on" --play/pause Audio button
  button_type: "off" --next button
  button_type: "stop" --middle button
  button_type: "raise"
  button_type: "lower"

  action: press
  action: release
"""

class PicoRemote(hass.Hass):

  serials = {}

  def initialize(self):
    global start_press
    global stop_press
    global previous_press
    start_press = time.time()
    stop_press = time.time()
    PicoRemote.serials = self.args
    self.listen_event(self.play_pause, "lutron_caseta_button_event")
    self.log("initialization complete, lutron pico remotes.")

  def play_pause(self, event, data, kwargs):
    # self.log("button press triggered.")
    global start_press
    global stop_press
    if data["action"] == "press":
      start_press = time.time()
    else:
      stop_press = time.time()
      duration = stop_press - start_press
      if duration > 0.4:
        self.log("long press detected")
        shuffle = "select_source"
      else:
        shuffle = "shuffle_set"
      # self.log(delay)
      button_name = data["button_type"]
      default_player = PicoRemote.serials[data["serial"]]
      actions = {
          "on": "media_play_pause", 
          "off": "media_next_track", 
          "stop": shuffle, 
          "raise": "volume_set",
          "lower": "volume_set"
        }
      action = actions[button_name]
      vol_change = 0.0
      sensitivity = duration/7
      if button_name == "raise":
        vol_change = sensitivity
      elif button_name == "lower":
        vol_change = -1*sensitivity
      self.call_service("speakers/control", data={"default": default_player, "action": action, "vol_change": vol_change})
      




