from chatsim.utils import Annotation, DiagAct, Goal, UserGoal
from random import choice


class TemplateNLG(object):

    def __init__(self):
        pass

    def get_utterance(self, annot_list):
        output_text_list = []
        for annot in annot_list:
            output_text_list.append(self.annot2text(annot))

        return ' '.join(output_text_list).strip()

    def _get_entity_value_text(self, goal):
        val_text = ''
        if goal.type == 'fixed' or goal.type == 'flexible' or goal.type == 'open':
            val_text = str(goal.value[0])
        else:
            val_text = ' or '.join(goal.value)

        return val_text

    def annot2text(self, annotation):
        output_text = ''
        if annotation.diagact.name == 'INFORM':
            goal_list = annotation.goal_list
            ent_val_tuples = []
            if goal_list:
                for goal in goal_list:
                    entity = goal.slot
                    value = self._get_entity_value_text(goal)
                    if entity == 'num_people':
                        ent_val_tuples.append(('number of people', value))
                    elif entity == 'theatre_name':
                        ent_val_tuples.append(('theater', value))
                    else:
                        ent_val_tuples.append((entity, value))

            output_text = ' '.join(['{} is {}'.format(ent, val) for (ent, val) in ent_val_tuples]).strip()

        if annotation.diagact.name == 'REQUEST':
            temp = 'what is '
            goal = annotation.goal_list[0]
            entity = goal.slot
            if entity == 'num_people':
                output_text = temp + 'number of people ?'
            elif entity == 'theatre_name':
                output_text = temp + 'theater ?'
            else:
                output_text = temp + entity + ' ?'

        if annotation.diagact.name == 'GREETING':
            output_text = choice(['hi', 'hello'])

        if annotation.diagact.name == 'AFFIRM':
            output_text = choice(['that is right', 'yes'])

        return output_text
