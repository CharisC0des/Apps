import appdaemon.plugins.hass.hassapi as hass

class GarageLights(hass.Hass):

  def initialize(self):
    self.listen_state(self.synch_lights, "light.light")
    self.log("initialization complete, garage lights.")

  def synch_lights (self, entity, attribute, old, new, kwargs):
    was_on = self.get_state("switch.garage_light")
    light_on = self.get_state("light.light")
    if light_on == "on" :
      if was_on == "off" :
        self.log("light was off - turning on")
        self.turn_on("switch.garage_light")
    elif light_on == "off" :
      if was_on == "on" :
        self.log("light was on - turning off")
        self.turn_off("switch.garage_light")
    self.log("trigger complete, garage lights.")
