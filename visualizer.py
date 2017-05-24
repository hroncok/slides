import random
import math

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter
from kivy import graphics
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.clock import Clock

import pygit2


class VisualizationApp(App):
    def __init__(self):
        super().__init__()
        self.blob_widgets = {}
        Clock.schedule_interval(self.update, 1/30)
        self.repo = pygit2.Repository('.')

    def build(self):
        self.layout = RelativeLayout()

        self.rescan()

        return self.layout

    def add_blob_widget(self, blob):
        widget = BlobWidget(
            blob,
            x=self.layout.width/2, y=self.layout.height/2,
        )
        self.layout.add_widget(widget)
        self.blob_widgets[blob.id] = widget
        return widget

    def update(self, t):
        for blob in self.blob_widgets.values():
            for other in self.blob_widgets.values():
                fx, fy = self.interaction(blob, other)

                # Attraction to center
                fx += ((self.layout.width/2 - blob.x) / self.layout.width) ** 3
                fy += ((self.layout.height/2 - blob.y) / self.layout.height) ** 3

                if not blob._touches:
                    blob.x += fx * t * 5
                    blob.y += fy * t * 5

                if blob.x < 0:
                    blob.x = 0
                if blob.y < 0:
                    blob.y = 0
                if blob.x > self.layout.width:
                    blob.x = self.layout.width
                if blob.y > self.layout.height:
                    blob.y = self.layout.height

    def interaction(self, obj, obj2):
        fx = fy = 0
        if obj is obj2:
            return 0, 0
        dx = obj.x - obj2.x
        dy = obj.y - obj2.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if not distance:
            rx = random.random() - 0.5
            ry = random.random() - 0.5
            obj.x += rx * obj.radius * 5
            obj.y += ry * obj.radius * 5
            return 0, 0
        ndx = dx / distance
        ndy = dy / distance
        if distance < 20:
            fx += ndx * 1e3
            fy += ndy * 1e3
        else:
            # Repulsion
            repulsion = 1e7 / distance ** 3
            fx += ndx * repulsion
            fy += ndy * repulsion

        #for edge in self.edges.get((obj, obj2), {}).values():
            #dfx, dfy = edge.force(distance, ndx, ndy, dx, dy)
            #fx += dfx
            #fy += dfy
        #for edge in self.edges.get((obj2, obj), {}).values():
            #dfx, dfy = edge.force(distance, -ndx, -ndy, -dx, -dy)
            #fx -= dfx
            #fy -= dfy
            #if obj2.reachable:
                #obj.reachable = max(obj.reachable, obj2.reachable) * 0.9
        return fx, fy

    def rescan(self):
        unvisited = set(self.blob_widgets)
        visited = set()

        def _scan(blob):
            print('scan', blob.id)
            if blob.id in visited:
                return
            else:
                visited.add(blob.id)

            if blob.id in unvisited:
                unvisited.discard(blob.id)
            else:
                self.add_blob_widget(blob)

            if isinstance(blob, pygit2.Tree):
                for child in blob:
                    _scan(child)
            elif isinstance(blob, pygit2.Commit):
                _scan(blob.tree)

        if self.repo.head:
            _scan(self.repo.head.peel())

        for old_id in unvisited:
            raise ValueError('old object')


class BlobWidget(Scatter):
    size_hint = None, None
    def __init__(self, blob, **kwargs):
        kwargs.setdefault('size', (50, 50))
        super().__init__(**kwargs)
        #self.bind(pos=self.update_canvas)
        #self.bind(size=self.update_canvas)
        #self.update_canvas()
        self.pos = 0, 0

        if isinstance(blob, pygit2.Tree):
            color = 1/2, 1, 1/2
        elif isinstance(blob, pygit2.Blob):
            color = 1/2, 1/2, 1/2
        elif isinstance(blob, pygit2.Commit):
            color = 1/2, 1/2, 1
        else:
            color = 1, 1/2, 1/2

        r = self.radius = self.size[0] / 2

        with self.canvas.before:
            graphics.Color(*color)
            self.bg_ellipse = graphics.Ellipse(pos=(-r, -r), size=self.size)

        label = Label(
            text=blob.hex[:5],
            x=-r, y=-r, size=self.size,
            color=(0, 0, 0, 0),
            valign='center', halign='center',
            font_name='LiberationMono-Bold',
        )
        self.add_widget(label)

        self.bg_ellipse.angle_end = 0
        Animation(angle_end=360, duration=0.2).start(self.bg_ellipse)
        Animation(color=(0, 0, 0, 1), duration=0.1).start(label)


    def collide_point(self, x, y):
        r = self.size[0]/2
        x +=  - self.pos[0]
        y +=  - self.pos[1]
        return x**2 + y**2 < r ** 2


VisualizationApp().run()
