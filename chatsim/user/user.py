from pathlib import Path
from chatsim.utils import Goal, UserGoal, read_user_profile
from random import choice

entity_value_sets = {
    'time': ['2', '3', '12', '7', '2 pm', '12 pm', '7 pm', '12 am', '7 am'],
    'date': ['today', 'tomorrow', 'saturday', 'monday', 'tuesday', 'wednesday', 'friday'],
    'movie': ['achcham yenbadhu madamaiyada', '12 angry men', 'a man called love', 'american pastoral', 'avatar'],
    'theatre_name': ['amc mercado', 'aquarius', 'lincoln square cinemas', 'angelika', 'the stanford theater'],
    'num_people': ['1', '2', '3', '4']
}
entity_types = ['fixed', 'flexible', 'multiple_value', 'open']
# entity_types = ['fixed', 'flexible']


class User():

    def __init__(self, name='Mansour', user_profile=None):
        self.name = name
        self.user_profile = user_profile
        self.user_goals = []

    def create_random_user_goals(self, num_of_goals: int = 100):
        for _ in range(num_of_goals):
            self.user_goals.append(self._create_random_user_goal())

    def _create_random_user_goal(self):
        user_goals = []
        for entity in list(entity_value_sets.keys()):
            created_goal = self._create_random_goal(entity)
            user_goals.append(created_goal)

        new_user_goal = UserGoal(goal_list=user_goals, domain='movie', intent='booking')

        return new_user_goal

    def _create_random_goal(self, entity: str):
        ent_type = choice(entity_types)
        ent_val = []
        if ent_type == 'fixed' or ent_type == 'flexible':
            ent_val.append(choice(list(entity_value_sets[entity])))
        elif ent_type == 'open':
            ent_val.append('dont care')
        elif ent_type == 'multiple_value':
            ent_val = list(entity_value_sets[entity])[:3]

        new_goal = Goal(slot=entity, value=ent_val, type=ent_type)

        return new_goal


def main():
    sample_user_profile = read_user_profile(Path('.') / 'sample_user_profile.yml')
    # print(sample_user_profile)
    mansour = User(user_profile=sample_user_profile)

    mansour.create_random_user_goals(num_of_goals=1000)

    print(mansour.user_profile)
    for g in mansour.user_goals:
        print(g)
        print()


if __name__ == "__main__":
    main()


# Goal = namedtuple('Goal', ['slot', 'value', 'type'])
# # User Goal
# UserGoal = namedtuple('UserGoal', ['domain', 'intent', 'goal_list'])
# # Annotation
# Annotation = namedtuple('Annotation', ['diagact','goal_list', 'intent', 'domain'])
# # DiagAct
# DiagAct = namedtuple('DiagAct', ['name', 'priority'])
