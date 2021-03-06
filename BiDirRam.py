from __future__ import generators
import plus
import AI
from AI import vector3
import Arenas
import Gooey
import math
import Tactics

class BiDirRam(AI.SuperAI):
    "For rammers with weapons in both front and back.  Dynamically switches directions and attacks with whichever side has more weapons."
    # Use 'weapons' to indicate weapons in the front, and 'sweapons' to indicate weapons in the back.
    name = "BiDirRam"

    def __init__(self, **args):
        AI.SuperAI.__init__(self, **args)

        self.zone = "weapon"
        self.sweapons = []               # used to track our secondary weapons
        self.triggers = ["Fire"]
        self.trigger2 = ["Srimech"]
        self.reloadTime = 0
        self.reloadDelay = 3
        self.currentTactic = 0
        self.spin_range = 3.0

        if 'sweapons' in args: self.sweapons = list(args['sweapons'])

        if 'range' in args:
            self.spin_range = args.get('range')

        if 'triggers' in args: self.triggers = args['triggers']
        if 'reload' in args: self.reloadDelay = args['reload']

        self.triggerIterator = iter(self.triggers)

        self.tactics.append(Tactics.Ram(self))
        #self.tactics.append(Tactics.Shove(self))

    def Activate(self, active):
        if active:
            if AI.SuperAI.debugging:
                self.debug = Gooey.Plain("watch", 0, 75, 100, 75)
                tbox = self.debug.addText("line0", 0, 0, 100, 15)
                tbox.setText("Throttle")
                tbox = self.debug.addText("line1", 0, 15, 100, 15)
                tbox.setText("Turning")
                tbox = self.debug.addText("line2", 0, 30, 100, 15)
                tbox.setText("")
                tbox = self.debug.addText("line3", 0, 45, 100, 15)
                tbox.setText("")
            #self.tauntbox = Gooey.Plain("taunt", 10, 175, 640, 175)
            #tbox = self.tauntbox.addText("taunt1", 10, 0, 640, 15)
            #tbox.setText("")

            self.RegisterSmartZone(self.zone, 1)

        return AI.SuperAI.Activate(self, active)

    def Tick(self):
        #self.tauntbox.get("taunt1").setText("Nose: " + str(self.fNoseOffset))
        # Turn around if there are more weapons on the back
        if len(self.weapons) < len(self.sweapons) and self.currentTactic == 0:
            tactic = [x for x in self.tactics if x.name == "Ram"]
            if len(tactic) > 0:
                self.tactics.remove(tactic[0])
                self.tactics.append(Tactics.ReverseRam(self))
                self.currentTactic = 1
        # Turn around again if there are more weapons in the front
        if len(self.sweapons) < len(self.weapons) and self.currentTactic == 1:
            tactic = [x for x in self.tactics if x.name == "ReverseRam"]
            if len(tactic) > 0:
                self.tactics.remove(tactic[0])
                self.tactics.append(Tactics.Ram(self))
                self.currentTactic = 0

        # spin up depending on enemy's range
        enemy, range = self.GetNearestEnemy()

        if enemy is not None and range < self.spin_range:
            self.Input("Spin", 0, 1)
        elif self.GetInputStatus("Spin", 0) != 0:
            self.Input("Spin", 0, 0)

        targets = [x for x in self.sensors.itervalues() if x.contacts > 0 \
            and not plus.isDefeated(x.robot)]

        # slight delay between firing
        if self.reloadTime > 0: self.reloadTime -= 1

        if len(targets) > 0 and self.reloadTime <= 0:
            try:
                trigger = self.triggerIterator.next()
            except StopIteration:
                self.triggerIterator = iter(self.triggers)
                trigger = self.triggerIterator.next()

            self.Input(trigger, 0, 1)
            self.reloadTime = self.reloadDelay

        return AI.SuperAI.Tick(self)

    def Throttle(self, throttle):
        # if we're car steering and we're not moving much, throttle up
        if self.bCarSteering and self.last_turn_throttle != 0:
            speed = self.GetSpeed()
            if speed > 0 and speed < self.top_speed / 3: throttle = self.last_throttle + 10
            elif speed < 0 and speed > -self.top_speed / 3: throttle = self.last_throttle - 10

        if self.currentTactic == 0:
            throttle = min(max(throttle, -100), 100)
        if self.currentTactic == 1:
            throttle = -min(max(throttle, -100), 100)

        if self.bInvertible and self.IsUpsideDown(): throttle = -throttle

        self.set_throttle = throttle
        self.Input('Forward', 0, throttle)
        self.DebugString(0, "Throttle = " + str(int(throttle)))

    def Turn(self, turning):
        if self.currentTactic == 0:
            turning = min(max(turning, -100), 100)
        if self.currentTactic == 1:
            turning = -min(max(turning, -100), 100)

        if self.bInvertible and self.IsUpsideDown(): turning = -turning

        self.set_turn_throttle = turning
        self.Input('LeftRight', 0, -turning)
        self.Input('LeftRight', 1, turning)
        self.DebugString(1, "Turning = " + str(int(turning)))

    def InvertHandler(self):
        # fire all weapons once per second (until we're upright!)
        while 1:
            for trigger in self.trigger2:
                self.Input(trigger, 0, 1)

            for i in range(0, 8):
                yield 0

    def LostComponent(self, id):
        # if we lose all our weapons, stop using the Ram tactic and switch to ReverseRam
        if id in self.weapons: self.weapons.remove(id)
        if id in self.sweapons: self.sweapons.remove(id)

        return AI.SuperAI.LostComponent(self, id)

    def DebugString(self, id, string):
        if self.debug:
            if id == 0: self.debug.get("line0").setText(string)
            elif id == 1: self.debug.get("line1").setText(string)
            elif id == 2: self.debug.get("line2").setText(string)
            elif id == 3: self.debug.get("line3").setText(string)

AI.register(BiDirRam)