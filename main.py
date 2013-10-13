import cymunk as cy
import math
from os.path import dirname, join
from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, Rectangle, PopMatrix, PushMatrix, Rotate, Translate, Line
from kivy.uix.widget import Widget
from kivy.properties import DictProperty, ListProperty
from kivy.core.image import Image
from random import random
from kivy.lang import Builder
from kivy.vector import Vector 
from kivy.core.window import Window
from kivy.uix.scatter import ScatterPlane

Builder.load_string('''
<Playground>:
    label: label
    rect_label: rect_label
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: label
            text: '0'
        Label:
            id: rect_label
            text: ''
''')

class Playground(Widget):

    cbounds = ListProperty([])
    cmap = DictProperty({})
    blist = ListProperty([])
    rects = ListProperty([])

    def __init__(self, **kwargs):
        self._hue = 0
        super(Playground, self).__init__(**kwargs)
        self.init_physics()
        self.bind(size=self.update_bounds, pos=self.update_bounds)
        self.texture = Image(join(dirname(__file__), 'circle.png'), mipmap=True).texture
        self.add_ground()
        self.add_rectangle(220, 300, 200., 100.)
        self.add_rectangle(350, 400, 50., 100., color=(0., .5, .5))
        self.add_circle(450, 600, 50)
        self.add_circle(100, 600, 50)
        self.add_static_rect()
        with self.canvas:
            Color(1, 1, 1, 1)
            Line(points=[0, 300, 10000, 300], width=1)
            Line(points=[300, 0, 300, 10000], width=1)

        Clock.schedule_interval(self.step, 1 / 30.)

    def init_physics(self):
        # create the space for physics simulation
        self.space = space = cy.Space()
        space.iterations = 30
        space.gravity = (0, -100)
        space.sleep_time_threshold = 0.5
        space.collision_slop = 0.5

        # create 4 segments that will act as a bounds
        for x in xrange(4):
            seg = cy.Segment(space.static_body,
                    cy.Vec2d(0, 0), cy.Vec2d(0, 0), 10.0)
            seg.elasticity = 0.6
            #seg.friction = 1.0
            self.cbounds.append(seg)
            space.add(seg)

        # update bounds with good positions
        self.update_bounds()

    def update_bounds(self, *largs):
        assert(len(self.cbounds) == 4)
        a, b, c, d = self.cbounds
        x0, y0 = self.pos
        x1 = self.right
        y1 = self.top
        space = self.space
        self.space.remove(a)
        self.space.remove(b)
        self.space.remove(c)
        self.space.remove(d)
        a = cy.Segment(space.static_body,
                    cy.Vec2d(x0, y0), cy.Vec2d(x1, y0), 10.0)
        b = cy.Segment(space.static_body,
                    cy.Vec2d(x1, y0), cy.Vec2d(x1, y1), 10.0)
        c = cy.Segment(space.static_body,
                    cy.Vec2d(x1, y1), cy.Vec2d(x0, y1), 10.0)
        d = cy.Segment(space.static_body,
                    cy.Vec2d(x0, y1), cy.Vec2d(x0, y0), 10.0)
        self.space.add(a)
        self.space.add(b)
        self.space.add(c)
        self.space.add(d)
        self.cbounds = [a, b, c, d] 

    def step(self, dt):
        self.space.step(1 / 30.)
        self.update_objects()

    def update_objects(self):
        # We update circle object and rectangle object
        # separately as for rectangles we need also apply
        # angle change
        for body, rect, rot in self.rects:
            self.rect_label.text = "%s, %s, %s" % (body.position.x, body.position.y, math.degrees(body.angle))
            rect.center = (body.position.x, body.position.y)
            rect.rotation = math.degrees(body.angle)

        for body, obj in self.cmap.iteritems():
            p = body.position
            radius, color, rect = obj
            rect.pos = p.x - radius, p.y - radius
            rect.size = radius * 2, radius * 2

    def add_random_circle(self):
        self.add_circle(
            self.x + random() * self.width,
            self.y + random() * self.height,
            10 + random() * 50)

    def add_circle(self, x, y, radius):
        " Add new circle to playground "
        body = cy.Body(100, 1e5)
        body.position = x, y
        circle = cy.Circle(body, radius)
        circle.elasticity = 0.6
        #circle.friction = 1.0
        self.space.add(body, circle)

        with self.canvas.before:
            self._hue = (self._hue + 0.01) % 1
            color = Color(self._hue, 0.3, 1, mode='hsv')
            rect = Rectangle(
                texture=self.texture,
                pos=(self.x - radius, self.y - radius),
                size=(radius * 2, radius * 2))
        self.cmap[body] = (radius, color, rect)
        # remove the oldest one
        self.blist.append((body, circle))
            
    def add_rectangle(self, x, y, width, height, color=(1, 0, 0)):
        " Add new rectangle to the playground "
        moment = cy.moment_for_box(100., width, height)
        body = cy.Body(100, moment)
        body.position = x, y
        box = cy.Poly.create_box(body, size=(width, height))
        box.elasticity = 0.
        self.space.add(box, body)
        widget = ScatterPlane(pos=(0., 0.), size=(width, height))
        with widget.canvas:
            Color(*color)
            rect = Rectangle(pos=(0, 0), size=(width, height))
            
        self.rects.append((body, widget, rect))
        self.add_widget(widget)

    def add_static_rect(self):
        " Add new static rectangle "
        body = cy.Body()
        box = cy.Poly.create_box(body, size=(200., 100.))
        box.elasticity = 0.
        body.position = 400., 100.
        self.space.add(box)
        widget = ScatterPlane(size=(200., 100.))
        with widget.canvas:
            Color(0., 1, 0, 1)
            Rectangle(pos=(0, 0), size=(200, 100))
            
        self.add_widget(widget)
        widget.center = body.position.x, body.position.y  

    def add_ground(self):
        body = cy.Body()
        box = cy.Poly.create_box(body, size=(Window.width, 2.))
        box.elasticity = 1.0
        body.position = Window.width / 2., -1.
        self.space.add(box)

    def on_touch_down(self, touch):
        shape = self.space.point_query_first(cy.Vec2d(touch.x, touch.y))
        # show touched shape
        print shape
        self.label.text = str(shape)
                

class PhysicsApp(App):
    def build(self):
        return Playground()

if __name__ == '__main__':
    PhysicsApp().run()
