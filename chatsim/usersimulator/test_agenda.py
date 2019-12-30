from chatsim.utils import Annotation, DiagAct, Goal
from chatsim.utils.diagact import *
from chatsim.usersimulator import Agenda


# # Goal
# Goal = namedtuple('Goal', ['slot', 'value', 'metainfo'])
# # User Goal
# UserGoal = namedtuple('UserGoal', ['domain', 'intent', 'goal_list'])
# # Annotation
# Annotation = namedtuple('Annotation', ['diagact','goal_list', 'intent', 'domain'])
# # DiagAct
# DiagAct = namedtuple('DiagAct', ['name', 'priority'])


# # Annotation = namedtuple('Annotation', ['diagact','goal_list', 'intent', 'domain'])

def main():
    age = Goal(slot='age', value=12, metainfo=None)
    name = Goal(slot='name', value='mansour', metainfo=None)

    annot1 = Annotation(diagact=Greeting, goal_list=[age], intent=None, domain=None)
    annot2 = Annotation(diagact=Greeting, goal_list=[age, name], intent=None, domain=None)
    annot3 = Annotation(diagact=Greeting, goal_list=[name], intent=None, domain=None)
    annot4 = Annotation(diagact=Greeting, goal_list=[age, name], intent=None, domain=None)
    ag = Agenda()
    ag.push(annot1)
    ag.push(annot2)
    ag.push(annot3)
    ag.push(annot4)
    x = ag.search_agenda('GREETING', goal_slot_name='name')
    print(x)
    ag.remove_annotation(annot1)
    print(ag)


if __name__ == '__main__':
    main()
