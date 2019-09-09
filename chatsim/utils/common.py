# from m2m_core.scenario.goal_slot import GoalSlot

from collections import namedtuple
import yaml
import numpy as np
# Goal
Goal = namedtuple('Goal', ['slot', 'value', 'type'])
# User Goal
UserGoal = namedtuple('UserGoal', ['domain', 'intent', 'goal_list'])
# Annotation
Annotation = namedtuple('Annotation', ['diagact','goal_list', 'intent', 'domain'])
# DiagAct
DiagAct = namedtuple('DiagAct', ['name', 'priority'])


def read_user_profile(path):
    with open(path, 'r') as f:
        return yaml.load(f)

def get_random_number(dist = "uniform"):
	if dist == "uniform":
		return np.random.rand()


# class Annotation(object):
# 	"""
# 	Attributes:
# 		- diagact (DialogueAct)
# 		- goal_slot_list (list[GoalSlot]): 
# 		- intent (str)

# 	Raises:
# 		- TypeError: if diagact type is not DialogueAct
# 		- TypeError: if intent is passed, but its type is not string
# 	"""
	
# 	def __init__(self,diagact,goal_slot_list=[],intent=None):

# 		# check the diagact, intent and goal_slot_list types
# 		if not isinstance(diagact,DialogueAct):
# 			raise TypeError("diagact should be an instance of DialogueAct")
# 		if intent:
# 			if not isinstance(intent,str):
# 				raise TypeError("intent should be a string")
# 		if goal_slot_list:
# 			if not set(type(obj) for obj in goal_slot_list)=={type(GoalSlot())}:
# 				raise TypeError("goal_slot_list should contain a list of GoalSlot objects!")

# 		# setting attributes
# 		self._diagact = diagact
# 		self._goal_slot_list = goal_slot_list
# 		self._intent = intent

# 		# check that annotation makes sense
# 		# self._check_for_errors()

# 	def _check_for_errors(self):
# 		"""
# 		Check that created annotation has no error.
# 		Raises:
# 			- AnnotationError
# 		"""
# 		if self._diagact.type in ["INFORM","REQUEST","REQUEST_OPTIONS","REQUEST_ALTERNATIVES"]:
# 			# raise an error if goal slot list is empty
# 			raise AnnotationError("Annotation with {} diagact should have non-empty goal_slot_list!".\
# 								format(self._diagact.type))

# 	def __str__(self):
# 		s = ""
# 		s += "DialogAct={}".format(str(self.diagact)) + "\n"
# 		if self.intent:
# 			s += "Intent=" + str(self.intent) + "\n"
# 		for gs in self.goal_slot_list:
# 			s += str(gs) + " "
		
# 		return s
	
# 	def __eq__(self,other):

# 		if self.diagact!=other.diagact:
# 			return False
# 		# if both goal_slot lists are empty then they are equal
# 		if not self.goal_slot_list and not other.goal_slot_list:
# 			return True
# 		# if only one of them is empty then they are not equal
# 		if not self.goal_slot_list or not other.goal_slot_list:
# 			return False
		
# 		if len(self.goal_slot_list)!=len(other.goal_slot_list):
# 			return False
# 		for gs in self.goal_slot_list:
# 			if gs not in other.goal_slot_list:
# 				return False
# 		return True

# 	# properties
# 	@property
# 	def diagact(self):
# 		return self._diagact
	
# 	@property
# 	def goal_slot_list(self):
# 		return self._goal_slot_list
	
# 	@property
# 	def intent(self):
# 		return self._intent
	
# class AnnotationError(Exception):
# 	def __init__(self,message):
# 		super().__init__(message)


# def main():
# 	annot = Annotation(diagact=Greeting, goal_list=[1,2,3], intent='book_restaurant', domain='restaurant')
# 	annot2 = Annotation(diagact=GoodBye, goal_list=[1,2,3], intent='book_restaurant', domain='restaurant')

# 	print(annot==annot2)

# if __name__ == '__main__':
# 	main()