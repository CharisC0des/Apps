import appdaemon.plugins.hass.hassapi as hass
class BoschKitchen(hass.Hass):

  appliances = {}
  recall_announcement = {}
  timer_announcement_handle = {}

  def initialize(self):
    self.appliances = {
      "oven door": self.get_entity("binary_sensor.bosch_hbl8753uc_68a40e35e446_bsh_common_status_doorstate"),
      "cooktop mode": self.get_entity("sensor.bosch_nitp669suc_68a40e49f847_bsh_common_status_operationstate"),
      "oven timer": self.get_entity("sensor.bosch_hbl8753uc_68a40e35e446_bsh_common_setting_alarmclock"),
      "cooktop timer": self.get_entity("number.bosch_nitp669suc_68a40e49f847_bsh_common_setting_alarmclock")
    }
    self.listen_state(self.timer_elapsed, self.appliances["oven timer"].entity_id, new="0")
    self.listen_state(self.timer_elapsed, self.appliances["cooktop timer"].entity_id, new="0")
    self.log("initialization complete, Bosch Kitchen.")
  

  def announce_timer_elapsed(self, kwargs):
    caller=kwargs["caller"]
    self.log(caller)
    blnContinue = True
    if caller == "Bosch cooktop":
      self.log (self.appliances["cooktop mode"].state)
      if self.appliances["cooktop mode"].state == "BSH.Common.EnumType.OperationState.Inactive" and self.recall_announcement[caller] > 0:
        blnContinue = False
        self.log("cooktop powered off, cancel timer reminders")
        self.cancel_timer(self.timer_announcement_handle[caller])
        self.recall_announcement[caller] = 0
    if blnContinue:
      msg = [f"{caller} timer elapsed"]
      if self.recall_announcement[caller] > 0:
        msg.extend([f" for {self.recall_announcement[caller]} minute"])
        if  self.recall_announcement[caller] > 1:
          msg.extend(["s"])
      self.log(msg)
      self.call_service("var/set", entity_id="var.tts_message", attributes={"message": "".join(msg)})
      self.call_service("script/overhead_announcement")
      self.log("announcement in progress")
      self.recall_announcement[caller] += 1

  def oven_door_opened(self, entity, attribute, old, new, kwargs):
    caller = "Bosch oven"
    self.log("oven door opened, cancel timer reminders")
    self.cancel_listen_state(self.oven_door)
    self.cancel_timer(self.timer_announcement_handle[caller])
    self.recall_announcement[caller] = 0

  def timer_elapsed (self, entity, attribute, old, new, kwargs):
    self.log(f"{entity} timer elapsed")    
    if 70 > int(old) > 0:
      call_entity = self.get_entity(entity)
      self.log("timer value: " + call_entity.state)
      if entity==self.appliances["oven timer"].entity_id:
        caller="Bosch oven"
        self.oven_door = self.listen_state(self.oven_door_opened, self.appliances["oven door"].entity_id, new="on")
      elif entity==self.appliances["cooktop timer"].entity_id:
        caller="Bosch cooktop" 
      self.recall_announcement[caller] = 0
      self.timer_announcement_handle[caller] = self.run_every(self.announce_timer_elapsed, "now", 60, caller=caller)
