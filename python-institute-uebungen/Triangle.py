from math import hypot


class Point:
    def __init__(self, x=0.0, y=0.0):
        self.__x = x
        self.__y = y
        

    def getx(self):
        return self.__x

    def gety(self):
        return self.__y

    def distance_from_xy(self, x, y):
        dis = hypot(self.__x - x,self.__y - y)
        return abs(dis)

    def distance_from_point(self, point):
        return self.distance_from_xy(point.getx(),point.gety())


class Triangle:
    def __init__(self, vertice1:Point, vertice2:Point, vertice3:Point):
       self.edge1 = vertice1
       self.edge2 = vertice2
       self.edge3 = vertice3

    def perimeter(self):
        length = 0
        length += self.edge1.distance_from_point(self.edge2)
        length += self.edge1.distance_from_point(self.edge3)
        length += self.edge3.distance_from_point(self.edge2) 
        return length


triangle = Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
print(triangle.perimeter())
