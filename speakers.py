import appdaemon.plugins.hass.hassapi as hass
import time
import re
from appdaemon.exceptions import TimeOutException

class Speakers(hass.Hass):
  announce = "off"
  speakers = {
    "kitchen": "media_player.bluesound_kitchen",
    "ensuite": "media_player.bluesound_ensuite",
    "naim": "media_player.bluesound_naim",
    "chromecast": "media_player.chromecast_hd",
    "bluesound": "media_player.bluesound"
  } 

  def initialize(self):
    self.register_service("speakers/make_announcement", self.make_announcement)
    self.register_service("speakers/control", self.control_speakers)
    self.log("speakers initialized.")
  
  def control_speakers(self, namespace, domain, service, kwargs):
    data = kwargs["data"]
    default_player = data["default"]
    action = data["action"]
    volume = data["vol_change"]
    self.log(f"Speaker control initiated for {default_player}; Action: {action}; Volume change: {str(volume)}")
    data = Speakers.check_speaker_status(self, default_player)
    player = self.get_entity(data["active_player"])
    service_data = {"entity_id":data["active_player"]}
    if action=="shuffle_set":
      service_data["shuffle"]= not(player.attributes.shuffle)
      self.log(service_data)
      pass
    elif action=="select_source":
      sources = dict(map(reversed, dict(enumerate(player.attributes.source_list)).items()))
      self.log(sources)
      i = sources.get(player.attributes.source, "")
      self.log(i)
      if i == "":
          i = sources.get('Library', 0)
      else:
        if i < len(sources)-1:
          i = i + 1
        else:
          i = 0
      service_data['source']= player.attributes.source_list[i]
    if volume != 0:
      self.log("adjusting volume")
      if data["active_player"] == data["master"]:
        self.log("adjusting volume on joined players")
        data["joined_players"].append(data["master"])
        for sp in data["joined_players"]:
          Speakers.adjust_volume(self, sp, volume, action)
      else:
        self.log("adjusting volume on active player")
        Speakers.adjust_volume(self, data["active_player"], volume, action)
    else:
      self.create_task(Speakers.wait_for_speakers(self, player.state, action, service_data))
      self.log(service_data)

  def check_speaker_status(self, default_player = Speakers.speakers["kitchen"]):
    data = {
      "active_players": [],
      "active_player": "",
      "joined_players": [],
      "master": ""
    }
    for sp in Speakers.speakers.values():
      speaker = Speakers.speaker_details(self, sp)
      artist_check = re.split(r'\s+', speaker.get("media_artist",""))
      if speaker.get("master","")==True:
        data["master"] = sp
      if len(artist_check)==3 and artist_check[1]=='+':
        data["joined_players"].append(sp)
      else:
        if speaker.get('state', "") == "playing":
          data["active_players"].append(sp)
    if data["active_players"] == []:
      self.call_service("bluesound/unjoin")
      data["active_player"] = default_player
    elif (default_player in data["active_players"]):
      if default_player in data["joined_players"]:
        data["active_player"] = data["master"]
      else:
        data["active_player"] = default_player
    else:
      if data["active_players"][0] in data["joined_players"]:
        data["active_player"] = data["master"]
      else:
        data["active_player"] = data["active_players"][0]
    self.log(data)
    return data

  async def wait_for_speakers(self, player_state, action, kwargs):
    if player_state == "idle":
      try:
        await player.wait_state("paused", timeout = 5)
      except TimeOutException:
        self.log(player.entity_id + " timed out")
    self.call_service(f"media_player/{action}", **kwargs) 
    self.log(action)
    

  def speaker_details(self, entity_id):
    speaker = self.get_entity(entity_id)
    state_data = {"state": speaker.state}
    for at in speaker.attributes:
      state_data[at] = speaker.attributes[at]
    # self.log(state_data)
    return state_data

  def adjust_volume(self, player, volume, action):
    curr_vol = self.get_state(player, attribute="volume_level")
    set_vol = curr_vol + volume
    if set_vol > 1:
      set_vol = 1
    elif set_vol < 0.1:
      set_vol = 0.1
    self.call_service(f"media_player/{action}", entity_id=player, volume_level=set_vol)


  async def make_announcement(self, namespace, domain, service, kwargs):
    data=kwargs["data"]
    self.log("Announcement called from "+ data["caller"]+". Message: "+ data["msg"]+"; Volume: "+str(data["volume_level"]))
    # Development in progress