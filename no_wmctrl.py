""" module Fake wmctrl
 (in case it's not present) """

class Window(object):
	id = '0x01FC0'

    @classmethod
    def get_active(cls):
    	return a_window

    @classmethod
    def by_id(cls, id):
    	return a_window

    def activate(self):
    	pass

a_window = Window()
