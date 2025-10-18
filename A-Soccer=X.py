# ba_meta require api 9
# can u see the mouse 😱🐀 take car of your self
# خلي بالك من الفار يمكن ياكل صباعك 😱🐀الرجاء الحظر منه
from __future__ import annotations
import math
import inspect
import babase
import random
import bauiv1 as bui
import bascenev1 as bs
from os import listdir
from bascenev1lib import maps
from typing import TYPE_CHECKING
from bascenev1lib.actor import playerspaz
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1 import get_foreground_host_activity as ga
if TYPE_CHECKING:
    from typing import Any, Sequence, Dict, Type, List, Optional, Union

""" Feel Free To Edit, it's All Yours <3 """
""" Discord: marwan_magdi """

textures_dir = listdir("ba_data/textures")
meshes_dir = listdir("ba_data/meshes")
textures = [i.split('.')[0] for i in textures_dir]
meshes =  [i.split('.')[0] for i in meshes_dir]

NormalPlayerSpaz = playerspaz.PlayerSpaz # storing the original spaz 

class NewPlayerSpaz(playerspaz.PlayerSpaz): # tweaked spaz class
    def __init__(self, player: bascenev1.Player, color: Sequence[float] = (1.0, 1.0, 1.0), highlight: Sequence[float] = (0.5, 0.5, 0.5), character: str = 'Spaz', powerups_expire: bool = True, start_invincible: bool = False):
        super().__init__(player=player,color=color,highlight=highlight,character=character, powerups_expire=powerups_expire)
        self.equip_boxing_gloves() # our pretty Ggoves
   
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.HitMessage): # if spaz is hitted
            self.node.handlemessage('flash') # emit a flash
            pass # no more.
        else:
            return super().handlemessage(msg)

class BallDiedMessage:
    def __init__(self, ball: Ball):
        self.ball = ball

class Ball(bs.Actor):
    def __init__(self, position: Sequence[float] = (0.0, 0.0, 0.0), is_area_of_interest: bool = True):
        super().__init__()
        activity = self.getactivity()
        assert activity is not None
        assert isinstance(activity, SoccerGame)
        self.scale = 1
        self.mesh_scale = self.scale*0.25
        self.gravity = 1.2
        shared = SharedObjects.get()
        ball_material = [shared.footing_material]
        ball_material = [shared.object_material, activity.ball_material]
        self.all_players_hitted: List[Player] = []
        self.all_players_touched: Dict[int, Player] = {}
        self.spawn_pos = (position[0], position[1]+0.6, position[2])
        self.node = bs.newnode('prop',delegate=self,attrs={
            'mesh': activity.ball_model, 
            'color_texture': activity.ball_tex, 
            'body': 'sphere', 
            'body_scale': self.scale, # the real colliding size
            'mesh_scale': self.mesh_scale, # the outside appearance 
            'reflection': 'soft', 
            'reflection_scale': [0], 
            'shadow_size': 3, 
            'is_area_of_interest': is_area_of_interest, 
            'position': self.spawn_pos, 
            'materials': ball_material, 
            'gravity_scale': 0 
            })
        bs.animate(self.node, 'mesh_scale', {0:0, 0.01:self.mesh_scale})

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            assert self.node
            self.node.delete()
            activity = self._activity()
            if activity and not msg.immediate: 
                activity.handlemessage(BallDiedMessage(self))
        elif isinstance(msg, bs.OutOfBoundsMessage):
            activity = self._activity()
            if activity.gk_mode:
                activity.handle_ball_wall_collide()
            assert self.node
            self.node.position = self.spawn_pos
        elif isinstance(msg, bs.HitMessage):
            assert self.node
            assert msg.force_direction is not None
            s_player = msg.get_source_player(Player)
            x = 1 # power multiplier
            if s_player is not None:
                activity = self._activity()
                if activity:
                    if s_player in activity.players:
                        self.all_players_touched[s_player.team.id] = s_player
                        self.all_players_hitted.append(s_player)
                        if activity.assistant_mode:
                            if activity.activated:
                                activity.left_right = 0
                                activity.up_down = 0
                                x = 1.2
                            else:
                                activity.left_right = 1
                                activity.up_down = 1
                                activity.assistant_setup()
            self.node.handlemessage('impulse',
                msg.pos[0], msg.pos[1], msg.pos[2],  
                msg.velocity[0]*x, msg.velocity[1]*x,  msg.velocity[2]*x, 
                msg.magnitude*x, 
                msg.velocity_magnitude*x,  0,  0,
                msg.force_direction[0],  msg.force_direction[1],msg.force_direction[2]
                )
        else:
            super().handlemessage(msg)
        impact = msg.velocity_magnitude * msg.magnitude
        if impact >= 1100:  # لو الضربة قوية

            # ضوء برتقالي مربوط بالكرة
            fire_light = bs.newnode('light', owner=self.node, attrs={
                'color': (1, 0.2, 0),
                'intensity': 1.2,
                'radius': 1.0
            })
            self.node.connectattr('position', fire_light, 'position')

            # يخفت تدريجيًا
            bs.animate(fire_light, 'intensity', {0: 1.2, 2.0: 0})
            bs.timer(2.0, fire_light.delete)

            # 🔥 مؤثر "شرر + دخان" متكرر يبان نار
            def fire_effect():
                if self.node:  # لو الكرة لسه موجودة
                    bs.emitfx(position=self.node.position,
                            count=30,
                            scale=3.5,
                            spread=0.5,
                            chunk_type='sweat')   # شرر
                    bs.emitfx(position=self.node.position,
                            count=10,
                            scale=0.7,
                            spread=0.3,
                            chunk_type='spark')   # دخان

            # نكرر التأثير ده كل 0.1 ثانية لمدة ثانيتين
            for t in range(20):
                bs.timer(0.1 * t, fire_effect)

            # صوت انفجار خفيف
            bs.getsound('explosion').play()





class Wall(bs.Actor):
    def __init__(self, position: Tuple[float, float, float]=(0,0,0), scale: Tuple[int, int, int]=(10,10,10)):
        super().__init__()
        activity = self.getactivity()
        self.node = bs.newnode('region',attrs={ 

            'position': position, 
            'scale': scale, 
            'type': 'box', 
            'materials': [activity.wall_material]
            })

class Dot(bs.Actor):
    def __init__(self, position: Tuple[float, float, float]=(0,0,0), size: List[int]=[0.3], color: Tuple[float, float, float]=(1,0,0)):
        super().__init__()
        activity = bs.getactivity()
        self.node = bs.newnode('locator', attrs={
            'shape':'circle',
            'color': color,
            'opacity':1, 
            'position': position, 
            'size': size, 
            'drawShadow': False
            })

class Text(bs.Actor):
    def __init__(self, text: Str='' , scale: Float=1.0, position: Tuple(Float, Float, Float)=(0,0,0), color: Tuple(Float, Float, Float)=(1,0,0), shadow: float=1.0, h_align=None, v_attach=None, in_world=True):
        super().__init__()
        activity = bs.getactivity()
        self.node = bs.newnode('text', attrs={
            'text': text,
            'color': color,
            'opacity':1, 
            'position': position, 
            'scale': scale, 
            'in_world': in_world,
            'shadow': shadow
            })
        if h_align is not None:
            self.node.h_align = h_align
        if v_attach is not None:
            self.node.v_attach = v_attach

    def delete(self) -> None:
        self.node.delete()

class Player(bs.Player['Team']):
    pass

class Team(bs.Team[Player]):
    def __init__(self) -> None:
        self.score = 0

# ba_meta export bascenev1.GameActivity
class SoccerGame(bs.TeamGameActivity[Player, Team]):

    creator = "\ue043 XERO Football Club \ue043" 
    name = 'XERO [Football-Champions]'
    description = f"Showup Your Soccer Skills\nin a Very Customizable Soccer Game \ue047.\n\n{creator}" 
    gk_easy, gk_medium, gk_hard = 300, 350, 380
    available_settings = [
    bs.IntSetting('Target Score',
        min_value=1,
        default=10,
        increment=1
        ),
    bs.IntChoiceSetting('Weather', choices=[
        #random
        ('Random 🎲', -1),

        ('Clear ☀️', 0),

        # Rain
        ('Light Rain 🌦️', 1),
        ('Medium Rain 🌧️', 2),
        ('Heavy Rain ⛈️', 3),

        # Snow
        ('Light Snow ❄️', 4),
        ('Medium Snow 🌨️', 5),
        ('Blizzard 🌪️', 6),

        # Storm
        ('Storm ⚡', 7),
        ('Thunderstorm ⛈️', 8),
        ('Mega Storm 🌩️', 9),
    ], default=0),
    bs.IntChoiceSetting('Game Time',choices=[
        ('None', 0),
        ('1 Minute', 60),
        ('2 Minutes', 120),
        ('5 Minutes', 300),
        ('10 Minutes', 600),
        ('20 Minutes', 1200)
        ],
       default=300
        ),
    bs.FloatChoiceSetting('Respawn Times',choices=[
        ('Shorter', 0.1),
        ('Short', 0.5),
        ('Normal', 1.0),
        ('Long', 2.0),
        ('Longer', 4.0)
        ],
        default=0.1
        ),
    bs.IntChoiceSetting('GK Practice Mode',choices=[
        ('Disabled', 0),
        ('Beginner', gk_easy),
        ('Amatuer', gk_medium),
        ('Intermediate', gk_hard),
        ],
        default=0
        ),
    bs.IntChoiceSetting('Ball Texture',choices=[
        ('Blue Stripes', 1),
        ('Orange Stripes', 2),
        ('Yellow Stripes', 3),
        ('Volley Ball', 4),
        ],
        default=1
        ),
    bs.BoolSetting('Epic SlowMotion', True),
    bs.BoolSetting('Map Limits (Invisible Walls)', True),
    bs.BoolSetting('Map Posters', True),
    bs.BoolSetting('Night Mode', True),
    bs.BoolSetting('Invincible Players', True),
    bs.BoolSetting('Icy Ground', False),
    bs.BoolSetting('Enable Pickup', False),
    bs.BoolSetting('Assisted Ball', False)]
    allow_pausing = False
    default_music = bs.MusicType.HOCKEY

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) 
 
    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return ['Soccer Stadium']     

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()

        # Game Modes
        self.gk_mode = int(settings['GK Practice Mode'])
        self.gk_level = {0:None, self.gk_easy:'Easy ★', self.gk_medium:'Medium ★★', self.gk_hard:'Hard ★★★'}[self.gk_mode]
        self.assistant_mode = bool(settings['Assisted Ball'])
        #حفظ الإعدادات
        self.weather_mode = int(settings['Weather'])
        if self.weather_mode == -1:  # يعني Random
            self.weather_mode = random.randint(0, 9)
        # Game Settings
        self.map_posters = bool(settings['Map Posters'])
        self.limited_map = bool(settings['Map Limits (Invisible Walls)'])
        self.invincible_mode = bool(settings['Invincible Players'])
        self.enable_pickup = bool(settings['Enable Pickup'])
        self.icy_ground = bool(settings['Icy Ground'])
        self.slow_motion = bool(settings['Epic SlowMotion'])
        self.night_mode = bool(settings['Night Mode'])
        self.score_to_win = int(settings['Target Score'])
        self.time_limit = float(settings['Game Time'])
        self.cheer_sound = bui.getsound('cheer')
        self.chant_sound = bui.getsound('crowdChant')
        self.foghorn_sound = bui.getsound('foghorn')
        self.swipsound = bui.getsound('swip')
        self.whistle_sound = bui.getsound('refWhistle')
        self.ball_textures = {
            1 : bs.gettexture('ouyaUButton'), 
            2 : bs.gettexture('ouyaIcon'), 
            3 : bs.gettexture('ouyaYButton'), 
            4 : bs.gettexture('gameCircleIcon'), 
            }
        self.ball_tex = self.ball_textures[int(settings['Ball Texture'])]
        self.ball_model = bs.getmesh('shield')
        self.ball_sound = bs.getsound('metalHit')
        self.emojis = ["\ue043","\ue04f",'\ue046','\ue048'] # for scoring suspense
        self.expressions = ['SUUIIII!','CALMA CALMA','BOOOM!','GOOOOAAL!']

        # Materials And Regions
        self.ball_material = bs.Material()
        self.ball_material.add_actions(
            actions=(('modify_part_collision','friction', 1.1)))
        self.ball_material.add_actions(
            conditions=('they_have_material',shared.pickup_material),
            actions=('modify_part_collision','collide', True))
        self.ball_material.add_actions(
            conditions=(('we_are_younger_than', 100),'and',('they_have_material', shared.object_material)),
            actions=('modify_node_collision', 'collide', True))
        self.ball_material.add_actions(
            conditions=('they_have_material',shared.footing_material),
            actions=('impact_sound',self.ball_sound, 0.2, 5))
        self.ball_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_connect', self.handle_ball_player_collide)))
        self.score_region_material = bs.Material()
        self.score_region_material.add_actions(
            conditions=('they_have_material', self.ball_material),
            actions=(('modify_part_collision', 'collide',True),
            ('call', 'at_connect', self.handle_score_gk_mode if self.gk_mode else self.handle_score)))
        self.wall_material = bs.Material()
        self.wall_material.add_actions(
            conditions=('they_have_material', self.ball_material),
            actions=(('modify_part_collision', 'collide',True),
            ('call', 'at_connect', self.handle_ball_wall_collide)))
        self.item_material = bs.Material()
        self.item_material.add_actions(
            actions=(
            ('modify_part_collision', 'collide', True),
            ('modify_part_collision', 'physical', True)))

        self.score_regions: Optional[List[bs.NodeActor]] = []
        self.ball_spawn_pos: Optional[Sequence[float]] = None
        self.ball: Optional[Ball] = None

        # Extras & Abbreviations
        self.red_dot_y = 9/1000 # Red Dot Height From Ground
        self.rainbow_animate = {0:(1,0,0), 0.5:(1,1,0), 1:(0,1,0), 1.5:(0,1,1), 2:(0,0,1), 2.5:(1,0,1), 3:(1,0,0)}
        self.bsd = 3.5 # Ball Spawn Delay
        ##########################################
        self.celebrater = 2 #وقت مخصص للاحتفال
        self.delete_text = 2 # مسح النص الاحتفالي
        ##########################################
        self.ctt = 0.03 # Scorer Text Transition Time
        self.att = self.ctt # Assister Text Transition Time (as the scorer)
        self.glt = 0.1 # Scorer Glow Transition Time
        self.gtt = self.ctt # "GOALLL!" Text Transition Time (as the scorer also)
        self.sgt = 0.2 # Scorer Glow Transition Time
        self.gd = "Welcome To XERO Football Club" # Game Beginning Description
        self.hdag = 'Score a Goal To Win' # Heading Description (a goal)
        self.hd = f"Score {self.score_to_win} Goals." # Heading Description (several goals)
        self.gmgd = f"Save Your Goal « LEVEL : {self.gk_level} »" # GK Mode Game Beginning Description 
        self.gmhd = f"Goal Keaper Mode « LEVEL : {self.gk_level} »"# GK Mode Heading Description 
        self.gmbsd = 0.5 # GK Mode Ball Spawn Delay
        self.activated = False # For Assistant Mode (A.M)
        self.left_right, self.up_down = 1, 1 # For A.M
        if self.gk_mode:
            self.tips = [bs.GameTip(
                'Shoot The Ball Towards Purple Lines So You Score.',
                icon=bs.gettexture('storeCharacter'),
                sound=bs.getsound('ding')
                )]
        else:
            self.scoreboard = Scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        shared = SharedObjects.get()
        self.team1 = self.teams[0]
        self.team2 = self.teams[1]
        goal1 = Wall(self.map.defs.boxes['goal1'][0:3], self.map.defs.boxes['goal1'][6:9])
        goal2 = Wall(self.map.defs.boxes['goal2'][0:3], self.map.defs.boxes['goal2'][6:9])
        goal1.node.materials = [self.score_region_material] 
        goal2.node.materials = [self.score_region_material] 
        self.score_regions.append(bs.NodeActor(goal1.node))
        self.score_regions.append(bs.NodeActor(goal2.node))
        # Small Credits For Me...
        self.credits = Text(f"{self.creator}",0.8,(0,0),(0,0,0),0,'center','bottom',False)
        bs.animate_array(self.credits.node, 'color', 3, self.rainbow_animate, loop=True)
        self.chant_sound.play()
        self.map_highlights()
        self.setup_standard_time_limit(self.time_limit)
        self.ball_spawn_pos = self.map.get_flag_position(None)
        if self.gk_mode:
            self.gk_setup() 
        else:
            self.update_scoreboard()
            self.spawn_ball()
            bs.timer(0.5, self.apply_weather)
            # في on_begin: شغّل السحابة أول مرة بعد 20 ثانية (بلا repeat)
            bs.Timer(20.0, bs.Call(self.spawn_cloud), repeat=True)



    # تابع: spawn_cloud مع إصلاحات
    def spawn_cloud(self):
        x = random.uniform(-8, 8)
        z = random.uniform(-5, 5)

        # سحابة خفيفة (جزيئات 'ice' تعطي لون أبيض ضبابي)
        bs.emitfx(
            position=(x, 10, z),
            count=15,
            scale=2.0,
            spread=1.0,
            chunk_type='ice'
        )

        # ضوء باهت يدي إحساس ضبابي
        try:
            cloud_light = bs.newnode('light', attrs={
                'position': (x, 9, z),
                'color': (0.8, 0.8, 0.85),
                'radius': 6.0,
                'intensity': 0.3,
                'height_attenuated': False
            })
            # نحذف الضوء بعد مدة قصيرة
            bs.timer(2.0, cloud_light.delete)
        except Exception:
            pass

        # جدولة الاستدعاء التالي بعشوائية (آمن)
        next_delay = random.uniform(15.0, 30.0)
        bs.timer(next_delay, self.spawn_cloud)




    def apply_weather(self):
        gnode = bs.getactivity().globalsnode

        if self.weather_mode == 0:  # clear
            gnode.tint = (1, 1, 1)
        # ===== RAIN =====
        elif self.weather_mode == 1:  # light rain
            self.start_rain(intensity=30, scale=0.4, speed=0.5)
        elif self.weather_mode == 2:  # medium rain
            self.start_rain(intensity=45, scale=0.6, speed=0.4)
        elif self.weather_mode == 3:  # heavy rain
            self.start_rain(intensity=75, scale=0.8, speed=0.3)

        # ===== SNOW =====
        elif self.weather_mode == 4:  # light snow
            self.start_snow(intensity=10, scale=0.6, speed=0.4)
        elif self.weather_mode == 5:  # medium snow
            self.start_snow(intensity=20, scale=0.8, speed=0.3)
        elif self.weather_mode == 6:  # blizzard
            self.start_snow(intensity=80, scale=0.6, speed=2)

        # ===== STORM =====
        elif self.weather_mode == 7:  # storm
            self.start_storm(light_freq=3, flash_intensity=2.0)
        elif self.weather_mode == 8:  # thunderstorm
            self.start_storm(light_freq=2, flash_intensity=3.0)
        elif self.weather_mode == 9:  # mega storm
            self.start_storm(light_freq=1, flash_intensity=5.0)

    def start_rain(self, intensity, scale, speed):
        def rain_effect():
            for i in range(intensity):
                x = random.uniform(-10, 10)
                z = random.uniform(-6, 6)
                bs.emitfx(position=(x, 10, z),
                        count=10,
                        scale=scale,
                        spread=1.0,
                        color=(0.5, 0.5, 1.0),  
                        chunk_type='ice')
        bs.Timer(speed, rain_effect, repeat=True)

    def start_snow(self, intensity, scale, speed):
        def snow_effect():
            for i in range(intensity):
                x = random.uniform(-10, 10)
                z = random.uniform(-6, 6)
                bs.emitfx(position=(x, 10, z),
                        count=15,
                        scale=scale,
                        spread=1.5,
                        chunk_type='ice')
        for t in range(60):
            bs.timer(speed * t, snow_effect)

    def start_storm(self, light_freq, flash_intensity):
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.2, 0.2, 0.3)

        def storm_light():
            flash = bs.newnode('light', attrs={
                'position': (0, 5, 0),
                'color': (1, 1, 1),
                'intensity': flash_intensity,
                'radius': 6.0
            })
            bs.timer(0.3, flash.delete)

        # نخليها تتكرر باستمرار
        def loop_lightning():
            storm_light()
            bs.timer(light_freq, loop_lightning)  # تتكرر كل شوية

        loop_lightning()
    
    def on_transition_in(self) -> None:
        super().on_transition_in()
        activity = bs.getactivity()
        gnode = bs.getactivity().globalsnode
        if self.night_mode:
            gnode.tint = (0.88, 0.77, 0.88)
            # gnode.tint = (0.72, 0.62, 0.72)
        if self.icy_ground:
            activity.map.is_hockey = True
        else:
            activity.map.is_hockey = False

    def spawn_player(self, player: Player) -> None:
        if self.invincible_mode:
            playerspaz.PlayerSpaz = NewPlayerSpaz
        else:
            playerspaz.PlayerSpaz = NormalPlayerSpaz
        spaz = self.spawn_player_spaz(player)
        if self.enable_pickup:
            spaz.connect_controls_to_player(enable_pickup=True)
        else:
            spaz.connect_controls_to_player(enable_pickup=False)
        #player.assigninput(babase.InputType.JUMP_PRESS, lambda: self.backflip_player(player))
        return spaz

    def handle_ball_player_collide(self) -> None:
        collision = bs.getcollision()
        try:
            ball = collision.sourcenode.getdelegate(Ball, True)
            player = collision.opposingnode.getdelegate(PlayerSpaz, True).getplayer(Player, True)
            ball.all_players_touched[player.team.id] = player
        except:
            return

    def handle_ball_wall_collide(self) -> None:
        collision = bs.getcollision()
        if not self.gk_mode:
            return 
        self.gk_saves_num_txt.node.text = str(int(self.gk_saves_num_txt.node.text)+1)
        self.update_score_gk_mode()
        self.kill_ball()
        bs.timer(self.gmbsd, self.gk_setup)

    def handle_score(self) -> None:
        assert self.score_regions is not None
        assert self.ball is not None 
        gnode = bs.getactivity().globalsnode
        region = bs.getcollision().sourcenode
        index = 0
        scorer_celebration_txt = random.choice(self.expressions) + ' ' + random.choice(self.emojis)
        for index in range(len(self.score_regions)):
            if region == self.score_regions[index].node:
                break
        scoring_team = None
        for team in self.teams:
            if team.id == index:
                team.score += 1
                scoring_team = team
                team_color = team.color
                for player in scoring_team.players:
                    if player.actor:
                        player.actor.handlemessage(bs.CelebrateMessage(self.celebrater))
                        #self.backflip_player(player)
                        #player.actor.node.handlemessage("celebrate_l", 1000) #Waving The Left Hand
                        #player.actor.node.handlemessage("celebrate_r", 1000) #Waving The Right Hand
                if (scoring_team.id in self.ball.all_players_touched and self.ball.all_players_touched[scoring_team.id]):
                    self.scorer = self.ball.all_players_touched[scoring_team.id]
                    self.stats.player_scored(self.scorer,100,color=team_color)
                    glow_color = (10, 10, 10)
                    prev_color = self.scorer.actor.node.color
                    bs.animate_array(self.scorer.actor.node, 'color', 3, {0:prev_color,self.sgt: glow_color,self.delete_text-self.sgt: glow_color,self.delete_text: prev_color})
                    try:
                        self.assister = self.ball.all_players_hitted[-2]
                        if self.scorer != self.assister and self.assister in scoring_team.players:
                            pos = self.assister.actor.node.position
                            self.stats.player_scored(self.assister, 70, color=team_color)
                            bs.broadcastmessage(f"Goal Scorer : {self.scorer.getname()}", color=(0,1,0)) 
                            bs.broadcastmessage(f"Assister : {self.assister.getname()}", color=(1,0.1,1))
                            self.assister_txt = Text( '💪🏻',0.01,(pos[0], pos[1]+1.25, pos[2]),shadow=2)
                            bs.animate(self.assister_txt.node, 'scale', {0:0, self.att:0.02, self.delete_text-self.att:0.02, self.delete_text:0})     
                            self.follow_assister()
                            bs.timer(self.delete_text, self.assister_txt.delete)
                        else:
                            bs.broadcastmessage(f"Goal Scorer : {self.scorer.getname()}", color=(0,1,0))
                    except:
                        bs.broadcastmessage(f"Goal Scorer : {self.scorer.getname()}", color=(0,1,0))
                    pos = self.scorer.actor.node.position
                    self.scorer_txt = Text(scorer_celebration_txt, 0.01, (pos[0], pos[1]+1.25, pos[2]), team_color,2)
                    bs.animate(self.scorer_txt.node, 'scale', {0:0, self.ctt:0.02, self.delete_text-self.ctt:0.02, self.delete_text:0})     
                    self.follow_scorer()
                    bs.timer(self.delete_text, self.scorer_txt.delete)
        goal_txt = Text('GOOOALLL!!',0.05, (-3.2, 0, -4), team_color,1.5)
        # Big Bang
        pos = bs.getcollision().position
        explosion = bs.newnode('explosion',attrs={
            'position': pos, 
            'color': team_color, 
            'radius':4 
            })
        try:
            self.spawn_goal_fire(pos, color=team_color, radius=4.0, flames=16, duration=2.5)
        except Exception:
            pass
        bs.animate(goal_txt.node, 'scale', {0:0, self.gtt:0.05, self.delete_text-self.gtt:0.05, self.delete_text:0})
        bs.timer(self.delete_text, goal_txt.delete)
        bs.animate_array(gnode, 'tint', 3, {0:gnode.tint, 0.07:(0,0,0) , 0.3:gnode.tint}) # darker tint for A glance
        bs.cameraflash(duration=1 if int(self.delete_text) < 1 else int(self.delete_text))
        self.foghorn_sound.play()
        self.cheer_sound.play()
        if scoring_team is not None:
            try:
                if scoring_team is self.teams[0]:
                    goal_pos = self.map.defs.boxes['goal2'][0:3]
                else:
                    goal_pos = self.map.defs.boxes['goal1'][0:3]

                gnode.camera_target = (goal_pos[0], goal_pos[1] + 2.0, goal_pos[2])
                gnode.camera_mode = "manual"

                def reset_camera():
                    gnode.camera_mode = "follow"
                    try:
                        center = self.map.get_flag_position(None)
                        gnode.camera_target = (center[0], center[1] + 1.0, center[2])
                    except Exception:
                        pass

                bs.timer(2.0, reset_camera)
            except Exception:
                pass
        self.update_scoreboard()
        self.kill_ball()
        if scoring_team.score >= self.score_to_win:
            self.end_game()
        print(f"⚽ {scoring_team.name} Score:", scoring_team.score)


    """ You Can Enable it When Scoring by Uncommenting The Line (443) """
    """ or When You Press Jump by Uncommenting The Line (384) """
    def backflip_player(self, player) -> None: # some suspens when score also when jump, like a backflip lol!
        pp = player.actor.node.position
        pv = player.actor.node.velocity
        pr = player.actor.node.run
        player.actor.node.handlemessage('impulse',pp[0],pp[1]-3,pp[2],pv[0],pv[1],pv[2],50*pr,10*pr,0,0,pv[0],pv[1],pv[2])
        player.actor.node.handlemessage('impulse',pp[0],pp[1]-4,pp[2],pv[0],pv[1],pv[2],50*pr,20*pr,0,0,pv[0],pv[1],pv[2])
        player.actor.node.handlemessage('impulse',pp[0],pp[1]-5,pp[2],0,10,0,50,20,0,0,0,10,0)
        bs.emitfx(chunk_type='sweat',position=pp,count=12,scale=3.0,spread=0.6)
        bs.emitfx(chunk_type='sweat',position=pp,velocity=(pv[0]*5,pv[1]*2,pv[2]), count=random.randrange(12,20), scale=2.4, spread=0.40)
        bs.emitfx(chunk_type='spark',position=pp,count=12,scale=1.0,spread=0.4)

    def follow_scorer(self) -> None:
        if not self.scorer_txt.node:
            return
        pos = self.scorer.actor.node.position
        self.scorer_txt.node.position = (pos[0], pos[1] + 1.5, pos[2])
        bs.timer(0, self.follow_scorer)

    def follow_assister(self) -> None:
        if not self.assister_txt.node:
            return
        pos = self.assister.actor.node.position
        self.assister_txt.node.position = (pos[0], pos[1] + 1.5, pos[2])
        bs.timer(0, self.follow_assister)

    def follow_label(self, player, label: Text) -> None:
            """Updates label position to stay above player. Stops when player or label gone."""
            try:
                # if label node removed -> stop
                if not getattr(label, 'node', None):
                    return
                # if player or his actor gone -> delete label and stop
                if not getattr(player, 'actor', None) or not getattr(player.actor, 'node', None):
                    try:
                        label.delete()
                    except:
                        pass
                    return
                pos = player.actor.node.position
                label.node.position = (pos[0], pos[1] + 1.5, pos[2])
                bs.timer(0, lambda: self.follow_label(player, label))
            except Exception:
                try:
                    label.delete()
                except Exception:
                    pass
    
#######################################################################################################
    def spawn_goal_fire(self, position , color=(1.0, 0.45 ,0.0), radius=3.0, flames=12, duration=2.0):
        """Spawn a ring of small explosison, sparks and flickering lights around 'position'."""
        nodes_to_cleanup = []

        def cleanup():
            for n in nodes_to_cleanup:
                try:
                    n.delete()
                except Exception:
                    pass
        #create flame in a circle
        for i in range(flames):
            ang = 2 * math.pi * i / flames
            fx_pos = (position[0] + math.cos(ang) * radius,
            position[1] + 0.6,
            position[2] + math.sin(ang) * radius)

            try:
                expl = bs.newnode('explosion', attrs={
                    'position': fx_pos,
                    'color': color,
                    'radius': 0.9
                })
                nodes_to_cleanup.append(expl)
            except Exception:
                pass
            
            try:
                bs.emitfx(chunk_type='spark', position=fx_pos, count=12, scale=3.1, spread=0.6)
            except Exception:
                pass
            

            try:
                light = bs.newnode('light', attrs={
                    'position': fx_pos,
                    'color': color,
                    'intensity': 1.2,
                    'radius': 0.6,
                    'height_attenuated': False
                })
                nodes_to_cleanup.append(light)

                bs.animate(light, 'intensity', {0: 1.4, duration * 0.4: 0.6, duration * 0.85: 1.0})
            except Exception:
                pass
            
        bs.timer(duration, cleanup)
        self._goal_fire_cleanup_timer=bs.Timer(int(duration * 1000), bs.Call(cleanup))
#######################################################################################################
    def follow_ball(self) -> None:
        ball = self.ball
        if ball is None:
            return
        pos = ball.node.position
        self.red_dot.node.position = (pos[0], self.red_dot_y, pos[2])
        if ball.node.gravity_scale == 0: # if gravity is zero
            if str(pos[0])[:5] != str(ball.spawn_pos[0])[:5]: # if The ball moved from it's spawn position a bit
                ball.node.gravity_scale = ball.gravity # restore the gravity to normal.
        bs.timer(0, self.follow_ball)
        
    def map_highlights(self) -> None:
        if self.gk_mode:
            gk_saves_txt = Text('Saves',0.03,(0.35, 2, -6),(0, 1, 0),1.5)
            gk_goals_txt = Text('Goals',0.03,(-2.2, 2, -6),(1, 0, 0),1.5)
            gk_total_txt = Text('Total',0.03,(3.9, 2, -6),(0.3, 1, 1),1.5)
            self.gk_saves_num_txt = Text('0',0.03,(1.1,1,-6),(0,1,0),1.5)
            self.gk_goals_num_txt = Text('0',0.03,(-1.5,1,-6),(1,0,0),1.5)
            self.gk_total_num_txt = Text('0.0%',0.03,(4, 1, -6),(1, 0, 0.1),1.5)
            front_wall = Wall((0, 5, -3), (50, 36, 0.5))
            near_wall = Wall((0, 5, 3), (50, 36, 0.5))
            mid_map_wall = Wall((-1, 5, 0), (0.5, 36, 20))
            dots_color = (1, 0, 1)
            y, z, x_start, x_end = 0.009, 2.45, -0.45, 8
            diameter = 0.1
            dots_len1 = int((-x_start+x_end)/diameter)
            dots_len2 = int(z/diameter)
            for i in range(0, dots_len1+1):
                Dot((x_start+i/(1/diameter), y, -z), [diameter], dots_color)
                Dot((x_start+i/(1/diameter), y, z), [diameter], dots_color)
            for i in range(0, dots_len2+1):
                Dot((x_start, y, z-i/(1/diameter)), [diameter], dots_color)
                Dot((x_start, y, -z+i/(1/diameter)), [diameter], dots_color)         
        elif self.map_posters:
            team1_txt = Text(self.team1.name,0.03,(-5.25, 2, -6),self.team1.color,1.5)
            team2_txt = Text(self.team2.name,0.03,(1.3, 2, -6),self.team2.color,1.5)
            self.team1_score_txt = Text(str(self.team1.score),0.035,(-1.1, 1, -6),self.team1.color,1.5)
            self.team2_score_txt = Text(str(self.team2.score),0.035,(0.5, 1, -6),self.team2.color,1.5)
            versis_txt = Text('VS',0.03,(-0.5, 2, -6),(1,1,1,0.7),1.5)
            colon_txt = Text(':',0.03,(-0.15, 1, -6),(1,1,1,0.7),1.5)
        if self.limited_map:
            x, y, z, v = 8.25, 0, 7, 20
            wall_scale = (0.5, 36, 10)
            right_goal_R = Wall((x, y, -z), wall_scale)
            right_goal_L = Wall((x, y, z), wall_scale)
            right_goal_T = Wall((x, y+v, z-z), wall_scale)
            left_goal_R = Wall((-x, y, z), wall_scale)
            left_goal_L = Wall((-x, y, -z), wall_scale)
            left_goal_T = Wall((-x, y+v, z-z), wall_scale)
        # Map Edges Light Spots
        pos1, pos2, pos3, pos4 = (-11.05, 0.3, -5.3), (11.9, 0.3, -4.04), (10.99, 0.3, 5.08), (-12, 0.3, 3.78)
        up_wall = [(pos1[0]+i, pos1[1], pos1[2]) if i < 22 else (pos1[0]+i-0.2, pos1[1], pos1[2]+0.1) for i in range(0, 23, 2)]
        right_wall = [(pos2[0], pos2[1], pos2[2]+i) for i in range(0, 9, 2)]
        down_wall = [(pos3[0]-i, pos3[1], pos3[2]) for i in range(0, 23, 2)]
        left_wall = [(pos4[0], pos4[1], pos4[2]-i) for i in range(0, 9, 2)]
        light_positions = [i for i in up_wall+right_wall+down_wall+left_wall]
        for light_pos in light_positions:
            light = bs.newnode('light', attrs={
                'position': light_pos,
                'color': (0, 0.8, 1),
                'intensity': 1.1,
                'radius': 0.16,
                'height_attenuated': True
                }) 
        # massive light in middle
        sun = bs.newnode('light', attrs={ 
            'position': (0,6,0),
            'color': (1, 1, 1),
            'intensity': 0.19,
            'radius': 3,
            'height_attenuated': False
            }) 

    def on_team_join(self, team: Team) -> None:
        pass

    def get_instance_description(self) -> Union[str, Sequence]:
        if self.gk_mode:
            return self.gmgd
        if self.score_to_win == 1:
            return self.gd
        return self.gd

    def get_instance_description_short(self) -> Union[str, Sequence]:
        if self.gk_mode:
            return self.gmhd
        if self.score_to_win == 1:
            return self.hdag
        return self.hd
#############################################################################################
    def end_game(self) -> None:                                                             
        """Create WIN/LOSE/DRAW labels above players, keep them visible for self.delete_text,
        then actually call self.end(results)."""
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)

        # توقعات النتيجة
        winner = None
        loser = None
        if len(self.teams) >= 2:
            t1, t2 = self.teams[0], self.teams[1]
            if t1.score > t2.score:
                winner, loser = t1, t2
            elif t2.score > t1.score:
                winner, loser = t2, t1
            else:
                winner = None  # draw
        else:
            winner = None
        
        if winner is None:
            # لو تعادل
            for team in self.teams:
                for player in team.players:
                    if getattr(player, 'actor', None) and getattr(player.actor, 'node', None):
                        pos = player.actor.node.position
                        lbl = Text('DRAW', 0.02, (pos[0], pos[1] + 1.5, pos[2]), (1, 1, 0), 2)
                        try:
                            bs.animate(lbl.node, 'scale', {0:0, 0.05:0.02, self.delete_text - 0.05:0.02, self.delete_text:0})
                        except Exception:
                            pass
                        bs.timer(0, lambda p=player, l=lbl: self.follow_label(p, l))
                        bs.timer(self.delete_text, lbl.delete)
        else:
            # الكسبان و الخسران
            for player in winner.players:
                if getattr(player, 'actor', None) and getattr(player.actor, 'node', None):
                    pos = player.actor.node.position
                    lbl = Text('Winner', 0.02, (pos[0], pos[1] + 1.5, pos[2]), (0, 1, 0), 2)
                    try:
                        bs.animate(lbl.node, 'scale', {0:0, 0.05:0.02, self.delete_text - 0.05:0.02, self.delete_text:0})
                    except Exception:
                        pass
                    bs.timer(0, lambda p=player, l=lbl: self.follow_label(p, l))
                    bs.timer(self.delete_text, lbl.delete)
            for player in loser.players:
                if getattr(player, 'actor', None) and getattr(player.actor, 'node', None):
                    pos = player.actor.node.position
                    lbl = Text('Loser', 0.02, (pos[0], pos[1] + 1.5, pos[2]), (1, 0, 0), 2)
                    try:
                        bs.animate(lbl.node, 'scale', {0:0, 0.05:0.02, self.delete_text - 0.05:0.02, self.delete_text:0})
                    except Exception:
                        pass
                    bs.timer(0, lambda p=player, l=lbl: self.follow_label(p, l))
                    bs.timer(self.delete_text, lbl.delete)
        
        if winner is not None:
            # نص في النص
            vs_label = bs.newnode('text',
                attrs={
                    'text': "|| \ue043 GAME OVER \ue043 ||",
                    'scale': 2.0,
                    'position': (0, 250),
                    'color': (1,1,1),
                    'h_align': 'center',
                    'v_attach': 'center'
                })
            bs.timer(5.0, vs_label.delete)

            # تلج كثييير ينزل
            def snow_effect():
                for i in range(50):
                    x = random.uniform(-10, 10)
                    z = random.uniform(-6, 6)
                    bs.emitfx(
                        position=(x, 10, z),
                        count=20,
                        scale=0.8,
                        spread=1.5,
                        chunk_type='ice'
                    )
            for t in range(25):
                bs.timer(0.2 * t, snow_effect)

            # 🎆 ألعاب نارية بألوان مختلفة
            def fireworks_effect():
                for i in range(6):
                    x = random.uniform(-8, 8)
                    z = random.uniform(-5, 5)
                    color = (random.random(), random.random(), random.random())
                    bs.emitfx(
                        position=(x, 1, z),
                        count=30,
                        scale=1.5,
                        spread=2.0,
                        chunk_type='spark'
                    )
                    bs.newnode('explosion', attrs={
                        'position': (x, 1, z),
                        'color': color,
                        'radius': 1.2
                    })
            for t in range(20):
                bs.timer(0.3 * t, fireworks_effect)


                # انهاء الللعبه
        end_delay = max(0.05, float(self.delete_text) + 0.05)
        bs.timer(end_delay, lambda: self.end(results=results))
#############################################################################################


    def update_scoreboard(self) -> None:
        if self.map_posters:
            try:
                self.team1 = self.teams[0]
                self.team1_score_txt.node.text = str(self.team1.score) 
                self.team2 = self.teams[1]
                self.team2_score_txt.node.text = str(self.team2.score) 
            except:
                pass
        win_score = self.score_to_win
        for team in self.teams:
            self.scoreboard.set_team_value(team, team.score, win_score)

    def create_red_dot(self) -> None:
        self.red_dot = Dot((0, self.red_dot_y, 0), [0.2])

    def kill_ball(self) -> None:
        self.red_dot.node.delete()
        self.ball = None

    def spawn_ball(self) -> None:
        if self.gk_mode:
            try:
                if not self.red_dot.node:
                    self.create_red_dot()
            except:
                self.create_red_dot()
            self.ball = Ball(position=(0, 0, 0), is_area_of_interest=False)
            self.follow_ball()
            return 
        self.swipsound.play()
        self.whistle_sound.play()
        assert self.ball_spawn_pos is not None
        self.ball = Ball(position=self.ball_spawn_pos,is_area_of_interest=True) 
        self.create_red_dot()
        self.follow_ball()

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(Player))
        elif isinstance(msg, BallDiedMessage):
            if self.gk_mode:
                return 
            if not self.has_ended():
                bs.timer(self.bsd, self.spawn_ball)
        else:
            super().handlemessage(msg)

    """———————————Assistant MODE (START)——————————— """
    """ Ball is Attached to You!, it's Not That Cool But i Was Just Bored so i Made it """
    def assistant_setup(self) -> None:
        if self.gk_mode:
            return 
        ball = self.ball
        if not ball:
            return 
        last_player = ball.all_players_hitted[0]
        pos = last_player.actor.node.position
        if not self.left_right or not self.up_down:
            self.activated = False
            return 
        self.left_right = last_player.actor.node.move_left_right/1.75
        self.up_down = last_player.actor.node.move_up_down/1.75
        if not self.left_right or not self.up_down:
            self.activated = False
            return 
        pos = (pos[0]+self.left_right, pos[1]+0.8, pos[2]-self.up_down)
        ball.node.position = pos
        self.activated = True
        bs.timer(0, self.assistant_setup)

    """———————————Assistant MODE (END)——————————— """

    """———————————GK MODE (START)——————————— """

    def gk_setup(self) -> None:
        if self.ball:
            self.kill_ball()
        self.spawn_ball()
        magnitude = random.randint(self.gk_mode, self.gk_mode+10)
        velocity_magnitude = self.gk_mode/6
        force_x = 15
        force_y = 3
        force_z = random.uniform(-2.7, 2.7)
        self.ball.node.handlemessage('impulse', 
            0,0,0,3,3,3, 
            magnitude,
            velocity_magnitude,
            0,0,
            force_x, force_y, force_z)

    def update_score_gk_mode(self) -> None:
        goals = int(self.gk_goals_num_txt.node.text)
        saves = int(self.gk_saves_num_txt.node.text)
        total = goals+saves
        percentage = saves/total
        new_txt = str(percentage*100)[:4]+'%' # just hate he 10 nums length number
        self.gk_total_num_txt.node.text = new_txt
        self.gk_total_num_txt.node.color = (1-percentage, percentage, 0.2)  # makin it goes to green when a good percent, red otherwise.

    def handle_score_gk_mode(self) -> None:
        self.kill_ball()
        self.gk_goals_num_txt.node.text = str(int(self.gk_goals_num_txt.node.text)+1)
        self.update_score_gk_mode()
        explosion_color = (random.random(), random.random(), random.random())
        explosion_radius = {self.gk_easy: 2, self.gk_medium: 3, self.gk_hard: 4}[self.gk_mode] # specific radius of explosion for the difficulty of game mode
        pos = bs.getcollision().position
        explosion = bs.newnode('explosion',attrs={
            'position': pos, 
            'color': explosion_color, 
            'radius': explosion_radius
            })
        bs.timer(self.gmbsd, self.gk_setup)
  
    """———————————GK MODE (END)——————————— """

class SoccerMap(maps.HockeyStadium):

    name = 'Soccer Stadium'
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'hockeyStadiumPreview'

    @classmethod
    def is_flat_ground(cls) -> bool:
        return True

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[int, Any] = {'meshes': (
            bs.getmesh('hockeyStadiumOuter'),
            bs.getmesh('hockeyStadiumInner'),
            bs.getmesh('hockeyStadiumStands')
            ),
            'vr_fill_mesh': bs.getmesh('footballStadiumVRFill'),
            'collision_mesh': bs.getcollisionmesh('hockeyStadiumCollide'), # posts & walls that collides
            'tex': bs.gettexture('hockeyStadium'), # floor & foreground texture
            'stands_tex': bs.gettexture('white'), # walls & background texture
            }
        material = bs.Material()
        data['ice_material'] = material
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        gnode = bs.getactivity().globalsnode
        self.use_fixed_vr_overlay = False
        self.node.materials = [shared.footing_material]
        self.floor.color = (0.05, 0.97, 0.05)
        gnode.floor_reflection = True
        gnode.floor_reflection = 2.5

bs._map.register_map(SoccerMap) # finally register the map to play.

""" Big Thanks To...ahhg Honestly Only Me Worked on it  """
"""Killer"""
