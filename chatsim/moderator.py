from chatsim.utils import Annotation
from chatsim.nlu.rasa.rasanlu import RasaNLU
from chatsim.chatbot.transformer_movie.chatbot import ChatBot
# from chatsim.chatbot.rule_based.chatbot import ChatBot

from chatsim.usersimulator.agenda_user import AgendaUser
from chatsim.user import User
from chatsim.nlg import TemplateNLG
from pathlib import Path
from chatsim.utils import Annotation, DiagAct, Goal, UserGoal, read_user_profile
import os
from chatsim.utils.diagact import *

CURRENT_DIR = Path(os.path.dirname(__file__))

MAX_TURNS = 15
NLU_MODEL_PATH = '/home/mansour/usersimulator/chatsim/nlu/rasa/trained_models/spacy_web_lg-tk_spacy-intent_sklearn-ner_spacy'
NLU_PROJECT = 'm2m-m'
NLU_MODEL = 'default_intent_classifier.yml'
NUMBER_OF_RUNS = 100

AGENDA_USER_PARAMS = {
    'max_turn': MAX_TURNS
}

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)


class Moderator(object):

    def __init__(self, user=None):
        self.chatbot = ChatBot()
        self.usersimulator = None
        self.nlu = RasaNLU()
        self.nlg = TemplateNLG()
        self.user = user
        self.default_metrics = {
            'success_rate': None,
            'mean_num_of_turns_per_conversation': None
        }
        self.logger = []
        self.current_user_goal = None

    def initialize(self, user):
        # initialize nlu
        self.nlu.get_server_response('', NLU_PROJECT, NLU_MODEL, port=5000)

        # initialize nlg


        # initialize usersimulator
        # self.usersimulator.initialize(user_goals=user.user_goals[0], user_profile=user.user_profile['Mansour'])

        # initialize chatbot
        # self.chatbot.get_response('')
    
    def simulate(self):
        # num of user goals is equal to num of runs
        num_of_successful_conversations = 0
        total_turns = 0
        for i in range(NUMBER_OF_RUNS):
            # print(self.user.user_goals[i])
            self.current_user_goal = self.user.user_goals[i]
            self.usersimulator.initialize(user_goals=self.current_user_goal, user_profile=self.user.user_profile['Mansour'])
            user_response = self.usersimulator.start_conversation()
            # print(user_response)
            user_utterance = self.nlg.get_utterance(user_response)
            # print(user_utterance)
            conversation_log = []
            conversation_log.append(('user',user_utterance))

            num_of_turns = 1
            episode_over = False
            failed = False
            while not episode_over:
                # get chatbot response
                # print('Getting CHATBOT RESPONSE')
                
                # give  the whole history to chatbot
                user_utterance = ' '.join([t[1] for t in conversation_log])
                # print(user_utterance)
                chatbot_response = self.chatbot.get_response(user_utterance.strip())
                conversation_log.append(('chatbot',chatbot_response))
                num_of_turns += 1                

                # pass chatbot response to NLU to get annotation
                # print('Getting NLU RESPONSE')
                chatbot_nlu_output = self.nlu.get_server_response(chatbot_response, NLU_PROJECT, NLU_MODEL, port=5000)
                chatbot_annotations = self._create_annotation(chatbot_nlu_output)
                # print(chatbot_nlu_output)
                # print(chatbot_annotations)
                
                # get usersimulator next response
                # print('Getting USER RESPONSE')
                user_response, episode_over, failed = self.usersimulator.next([chatbot_annotations], num_of_turns)
                user_utterance = self.nlg.get_utterance(user_response)
                conversation_log.append(('user',user_utterance))
                num_of_turns += 1                
                if failed:
                    break

            total_turns += num_of_turns
            self.chatbot.asked_entities = set()

            if (num_of_turns < MAX_TURNS-1) and (not failed):
                num_of_successful_conversations += 1
            print(conversation_log)
        
        
        self.logger.append(conversation_log)
        print('Mean number of turns is = {}'.format(total_turns/NUMBER_OF_RUNS))
        print('Success rate is = {}'.format(num_of_successful_conversations/NUMBER_OF_RUNS))


    def _create_annotation(self, nlu_output):
        diagact = None
        if nlu_output['intent']['name'] == 'INFORM':
            diagact = Inform
        elif nlu_output['intent']['name'] == 'REQUEST':
            diagact = Request
        elif nlu_output['intent']['name'] == 'GREETING':
            diagact = Greeting
        elif nlu_output['intent']['name'] == 'AFFIRM':
            diagact = Affirm
        elif nlu_output['intent']['name'] == 'NEGATE':
            diagact = Negate
        elif nlu_output['intent']['name'] == 'CONFIRM':
            diagact = Confirm
        elif nlu_output['intent']['name'] == 'THANK_YOU':
            diagact = ThankYou
        elif nlu_output['intent']['name'] == 'GOODBYE':
            diagact = GoodBye
        elif nlu_output['intent']['name'] == 'SELECT':
            diagact = Select
        elif nlu_output['intent']['name'] == 'NOTIFY_SUCCESS':
            diagact = NotifySuccess
        elif nlu_output['intent']['name'] == 'NOTIFY_FAILURE':
            diagact = NotifyFailure            

        goal_list = []
        for ent_val in nlu_output['entities']:
            entity = ent_val['entity']
            value = ent_val['value']
            goal_list.append(Goal(slot=entity,value=value,type=None))
        
        # fix nlu select
        if diagact.name=='SELECT':
            if not goal_list:
                text = nlu_output['text']
                if 'time' in text:
                    goal_list.append(Goal(slot='time',value='2 pm',type=None))
                if 'date' in text:
                    goal_list.append(Goal(slot='date',value='tomorrow',type=None))
                if 'movie' in text:
                    goal_list.append(Goal(slot='movie',value='12 angry men',type=None))
                if 'theater' in text:
                    goal_list.append(Goal(slot='theatre_name',value='angelika',type=None))
                if 'tickets' in text or 'people' in text:
                    goal_list.append(Goal(slot='num_people',value='2',type=None))


        return Annotation(diagact=diagact,goal_list=goal_list,intent='booking',domain='movie')



def main():
    # for _ in range(10):
    #     print(m.nlu.get_server_response('what time and date?', NLU_PROJECT, NLU_MODEL, port=5000))
    
    # create sample user to be used for user goals and user profile components
    
    sample_user_profile = read_user_profile(CURRENT_DIR / 'user/sample_user_profile.yml')
    mansour = User(user_profile=sample_user_profile)
    mansour.create_random_user_goals(num_of_goals=100)

    m = Moderator(user=mansour)
    # print(mansour.user_goals)
    # return
    # for _ in range(10):
    #     print(m.chatbot.get_response('hi , buy 3 movie tickets for tomorrow .'))

    # return


    user_simulator = AgendaUser(
            params=AGENDA_USER_PARAMS, 
            current_intent='booking'
        )
    m.usersimulator = user_simulator

    m.initialize(mansour)
    # print(m.usersimulator._agenda)

    # start simulation
    m.simulate()


if __name__ == "__main__":
    main()