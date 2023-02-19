import appdaemon.plugins.hass.hassapi as hass
from appdaemon.exceptions import TimeOutException
import asyncio
#register_service
#get_app()
#both ways to call app from another in app daemon
class BoschKitchen(hass.Hass):

  appliances={}
  
  def initialize(self):
    BoschKitchen.appliances = {
      "oven door": self.get_entity("binary_sensor.bosch_hbl8753uc_68a40e35e446_bsh_common_status_doorstate"),
      "cooktop mode": self.get_entity("sensor.bosch_nitp669suc_68a40e49f847_bsh_common_status_operationstate"),
      "oven timer": self.get_entity("number.bosch_hbl8753uc_68a40e35e446_bsh_common_setting_alarmclock"),
      "cooktop timer": self.get_entity("number.bosch_nitp669suc_68a40e49f847_bsh_common_setting_alarmclock")
    }
    # self.log(BoschKitchen.appliances)
    # for s in BoschKitchen.appliances.values():
    #   self.log(s.entity_id + ": " + s.state)
    self.listen_state(self.timer_elapsed, BoschKitchen.appliances["oven timer"].entity_id, new="0")
    self.listen_state(self.timer_elapsed, BoschKitchen.appliances["cooktop timer"].entity_id, new="0")
    self.log("initialization complete, Bosch Kitchen.")
  
  
  async def check_oven_door(self, entity, attribute, old, new, kwargs):    
    kwargs["recall"]+=1
    door_sensor = BoschKitchen.appliances["oven door"]
    try:
      await door_sensor.wait_state("on", timeout = 60)
      self.log("item removed")
    except TimeOutException:
      self.log("oven timer elapsed and item not removed, call announcement again")
      pass # didn't complete on time

  async def check_cooktop(self, entity, attribute, old, new, kwargs):   
    kwargs["recall"]+=1
    cooktop_powered = BoschKitchen.appliances["cooktop mode"]
    try:
      await cooktop_powered.wait_state("BSH.Common.EnumType.OperationState.Inactive", timeout = 60)
      self.log("cooktop turned off")
    except TimeOutException:
      self.log("cooktop timer elapsed and not turned off, call announcement again")
      pass # didn't complete on time

  def timer_elapsed (self, entity, attribute, old, new, kwargs):    
    if 10 > int(old) > 0:
      call_entity = self.get_entity(entity)
      self.log("timer value: "+call_entity.state)
      if call_entity.state=="0":
        #device_ID = entity.replace("number.", "").replace("_bsh_common_setting_alarmclock", "")
        if entity==BoschKitchen.appliances["oven timer"].entity_id:
          caller="Bosch oven"
        elif entity==BoschKitchen.appliances["cooktop timer"].entity_id:
          caller="Bosch cooktop"
        msg = [caller, " timer elapsed"]
        try:
          if kwargs["recall"] == 1:
            msg.extend([" for ", kwargs["recall"], " minute"])
          elif  kwargs["recall"] > 1:
            msg.extend([" for ", kwargs["recall"], " minutes"])
        except:
          kwargs = {"recall": 0}
          self.log("first timer reminder")
          pass
        self.log(msg)
        self.call_service("var/set", entity_id="var.tts_message", attributes={"message": "".join(msg)})
        self.call_service("script/overhead_announcement")
        self.log("announcement in progress")
        if caller == "Bosch oven":
          self.create_task(BoschKitchen.check_oven_door(self, entity, attribute, old, new, kwargs),timer_elapsed (self, entity, attribute, old, new, kwargs))
        elif caller == "Bosch cooktop":
          self.create_task(BoschKitchen.check_cooktop(self, entity, attribute, old, new, kwargs),timer_elapsed (self, entity, attribute, old, new, kwargs))
