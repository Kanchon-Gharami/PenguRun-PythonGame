def setup(scene):
    global SCENE
    SCENE = scene
    
import txppb
d = txppb.run(setup)
d.addBoth(print)

import ppb

class Penguin(ppb.Sprite):
    pass


SCENE.add(Penguin(pos=(0,0)))

from ppb import keycodes

DIRECTIONS = {keycodes.Left: ppb.Vector(-1,0), keycodes.Right: ppb.Vector(1,0),
              keycodes.Up: ppb.Vector(0, 1), keycodes.Down: ppb.Vector(0, -1)}

from mzutils import set_in_class

Penguin.direction = ppb.Vector(0, 0)

@set_in_class(Penguin)
def on_update(self, update_event, signal):
    self.position += update_event.time_delta * self.direction
    
Penguin.direction = DIRECTIONS[keycodes.Up]/4

Penguin.direction = ppb.Vector(0, 0)

@set_in_class(Penguin)
def on_key_pressed(self, key_event, signal):
    self.direction = DIRECTIONS.get(key_event.key, ppb.Vector(0, 0))    

@set_in_class(Penguin)
def on_key_released(self, key_event, signal):
    if key_event.key in DIRECTIONS:
        self.direction = ppb.Vector(0, 0)
        
class OrangeBall(ppb.Sprite):
    pass

SCENE.add(OrangeBall(pos=(-4, 0)))

OrangeBall.is_moving = False

@set_in_class(OrangeBall)
def kick(self, direction):
    self.target_position = self.position + direction
    self.original_position = self.position
    self.time_passed = 0
    self.is_moving = True

@set_in_class(OrangeBall)
def on_update(self, update_event, signal):
    if self.is_moving:
        self.position = self.target_position
        self.is_moving = False
        
ball, = SCENE.get(kind=OrangeBall)
ball.kick(ppb.Vector(1, 1))

from mzutils import smooth_step

@set_in_class(OrangeBall)
def maybe_move(self, update_event, signal):
    if not self.is_moving:
        return False
    self.time_passed += update_event.time_delta
    if self.time_passed >= 1:
        self.position = self.target_position
        self.is_moving = False
        return False
    t = smooth_step(self.time_passed)
    self.position = (1-t) * self.original_position + t * self.target_position
    return True

OrangeBall.on_update = OrangeBall.maybe_move

ball, = SCENE.get(kind=OrangeBall)
ball.kick(ppb.Vector(1, -1))

from mzutils import collide
import random

OrangeBall.x_offset = OrangeBall.y_offset = 0.25

@set_in_class(OrangeBall)
def on_update(self, update_event,signal):
    if self.maybe_move(update_event, signal):
        return
    penguin, = update_event.scene.get(kind=Penguin)
    if not collide(penguin, self):
        return
    try:
        direction = (self.position - penguin.position).normalize()
    except ZeroDivisionError:
        direction = ppb.Vector(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
    self.kick(direction)
    
class Target(ppb.Sprite):
    pass

SCENE.add(Target(pos=(4, 0)))

class Fish(ppb.Sprite):
    pass

@set_in_class(Target)
def on_update(self, update_event, signal):
    for ball in update_event.scene.get(kind=OrangeBall):
        if not collide(ball, self):
            continue
        update_event.scene.remove(ball)
        update_event.scene.add(OrangeBall(pos=(-4, random.uniform(-3, 3))))
        update_event.scene.add(Fish(pos=(random.uniform(-4, -3),
                                         random.uniform(-3, 3))))
        
Fish.x_offset = 0.05
Fish.y_offset = 0.2
@set_in_class(Fish)
def on_update(self, update_event,signal):
    penguin, = update_event.scene.get(kind=Penguin)
    if collide(penguin, self):
        update_event.scene.remove(self)
        

def set_in_class(klass):
    def retval(func):
        setattr(klass, func.__name__, func)
        return func
    return retval

def smooth_step(t):
    return t * t * (3 - 2 * t)

_WHICH_OFFSET = dict(
    top='y_offset',
    bottom='y_offset',
    left='x_offset',
    right='x_offset'
)

_WHICH_SIGN = dict(top=1, bottom=-1, left=-1, right=1)

def _effective_side(sprite, direction):
    return (getattr(sprite, direction) -
            _WHICH_SIGN[direction] *
           getattr(sprite, _WHICH_OFFSET[direction], 0))

def _extreme_side(sprite1, sprite2, direction):
    sign = -_WHICH_SIGN[direction]
    return sign * max(sign * _effective_side(sprite1, direction),
                      sign * _effective_side(sprite2, direction))
   
def collide(sprite1, sprite2):
    return (_extreme_side(sprite1, sprite2, 'bottom') <
            _extreme_side(sprite1, sprite2, 'top')
            and
            _extreme_side(sprite1, sprite2, 'left') <
            _extreme_side(sprite1, sprite2, 'right'))