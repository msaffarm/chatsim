import random as ra
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from chatsim.utils import Annotation, DiagAct, Goal, get_random_number
from chatsim.utils.diagact import *

import copy

class Agenda():
    """
    Agenda in agenda-based user simulator.
    Agenda is a stack-like data structure which we use to store user Constraints and Requests.

    Attributes:
        - data (list[Annotation]): Container for annotations in agenda
    """
    def __init__(self):
        # self._data = []
        self.stack = []

    def pop(self,number_of_items=1,multi_diagact=False):
        """
        Pop number_of_items annotations from the top of the agenda.
        
        Args:
            - number_of_items (int): number of items (annotations) to be poped from the agenda
            - multi_diagact (bool): Flag that controls if we pop annotations with mulitple diagacts
                from the agenda or not. If set False, then we only pop annotation with same diagact from the
                agenda (and stop when we reach an annotation with a different kind of diagact than what we prevoiously
                have popped). 
                If multi_diagact set True, then we pop number_of_items annotations regardless of whether their
                diagact type count is more than one.

        Returns:
            - popped_annotations (list[Annotation])

        """
        popped_annotations = []
        if not multi_diagact:
            if not self.is_empty():
                current_da = self.stack[-1].diagact.name
                prev_da = current_da
                while current_da==prev_da and number_of_items:
                    annot = self.stack.pop()
                    popped_annotations.append(annot)
                    if self.is_empty():
                        break
                    prev_da = annot.diagact.name
                    current_da = self.stack[-1].diagact.name
                    number_of_items -= 1
            
        else:
            while number_of_items and not self.is_empty():
                popped_annotations.append(self.stack.pop())
                number_of_items -= 1
        
        logger.debug("Successfully poped {} items from agenda".format(len(popped_annotations)))
        
        # we reverse the popped_annotations since we need to keep the order of items at the top of the agenda
        return popped_annotations[::-1]

    def remove_annotation(self,annotation):
        """
        remove annotation from the agenda
        """
        self.stack.remove(annotation)
    
    def remove_by_index(self,index_list):
        """
        Remove the annotations which their index is in the index_list

        Args:
            index_list (list(int))        
        """
        if not isinstance(index_list,list):
            raise TypeError("You have to pass a list of indices to remove from agenda!")

        new_agenda = []
        for i,annotation in enumerate(self.stack):
            if i not in index_list:
                new_agenda.append(annotation)
        
        self.stack = new_agenda

    def push(self, annotation):
        """
        Push annotation to the agenda.
        This function makes sure that the given annotation is not already in the agenda and if so,
        it removes it from the agenda and add annotation to the TOP OF THE AGENDA.
        Args:
            - annotation (Annotation)
        """
        if isinstance(annotation,list):
            for annot in annotation:
                self._update(annot)
        else:
            self._update(annotation)
    
    def _update(self, annotation):
        """
        If annotation is not already in self._data (or agenda) then push it tho the agenda
        Args:
            - annotation (Annotation)
        """
        if annotation in self.stack:
            self.stack.remove(annotation)
        self.stack.append(annotation)


    def search_agenda(self,diagact_type,goal_slot_name=None):
        """
        Find all the annotations with the given diagact and goal_slot_name and 
        return their index in the agenda
        Args:
            diagact_type (str): Diagact type
            goal_slot_name (str): Name of the GoalSlot object in the annotation

        Returns:
            index_list (list(int)): List of indices for the annotations with the given diagact
        """
        index_list = []
        for i, annotation in enumerate(self.stack):
            if annotation.diagact.name==diagact_type:
                if not goal_slot_name:
                    index_list.append(i)
                else:
                    if goal_slot_name in list(gs.slot for gs in annotation.goal_list):
                        index_list.append(i)
        
        return index_list

    def clear(self):
        self.stack.clear()

    def is_empty(self):
        return len(self.stack)==0


    def __len__(self):
        return len(self.stack)
    
    def __str__(self):
        s = ""
        for annotation in self.stack[::-1]:
            s += "-"*100 + "\n"
            s += "Diagact= {}, GoalSlots={}".format(annotation.diagact.name,
                str([(gs.slot,gs.value) for gs in annotation.goal_list])) +"\n"
        return s
    
    def __getitem__(self,index):
        return self.stack[index]


class AgendaUser(object):
    """
    Agenda based user simulator based on http://mi.eng.cam.ac.uk/~sjy/papers/stwy07.pdf
    This simulator is multi-domain and multi-intent user simulator. For every intention of the user
    we create an agenda and user can move between these agendas to simulate a multi-intent behaviour.

    Attributes:
        - max_turn (int): Maximum number of turns that user converses with the system
        - profile (Profile): User's profile. We simulate the behaviour of the user and condition the traditional
            agenda-based user simulator on user behaviour. (see tests/file/sample_user_profile.txt)
        - user_goals (dict{str:UserGoal}): A dictionary mapping intents to UserGoal objects. 
            A UserGoal object is a container for slot value pairs that user desires.
        - current_intent (str): Current intention of the user. This flag determined which agenda user uses when
            talking to the system.
        - agenda_dict (dict{str:Agenda}): To simulate a multi-intent user, we create an Agenda for each of the
            user intentions. User behaviour later will be used to determine how user switches between different
            Agendas (intentions) to simulate the multi-domain user.
    """
    def __init__(self,name=None,params=None, user_profile=None, user_goals=None, current_intent=None):
        self._max_turn = params["max_turn"]
        self._profile = user_profile
        self._user_goals = user_goals
        self._current_intent = current_intent
        # self._agenda_dict = {}
        self._agenda = Agenda()
        # self._intent_to_domain = {}
        # special memory items to keep track of user behaviour
        self._request_option_slots = set()
        self._informed_slots = set()

    def initialize(self,user_profile, user_goals):
        """
        Initialize agenda-based user.
        
        Args:
            - scenario (Scenario): Current scenario used in the conversation between the user and system.
                A scenario determines UserProfile (user's behaviour) and his UserGoal (A container of slot value pairs
                that user conveys to the system). We use UserGoals of a scenario to build Agendas for each user intent.
            - domain_dict (dict{str:Domain}): Mapping form domain names to Domain objects. Each Domain has a number
                of intentions which AgendaUser uses to get information about slots of that intention (see m2m_core/
                ontology/ontologies/movie_domain.yml for an example)
        
        The following steps happen in this function:
            1- UserProfile and UserGoal will be set from the current scenario.
            2- Get all the intentions from the current scenario which will be user's intentions for this conversation.
            3- Create agenda_dict for a the scenario (for each intent create an Agenda)
            4- Create a mapping from intent to domains
            5- For each intention, choose what slots to put from UserGoal in Agenda and create the Agenda using
              the selected slots.
        """
        # clear agenda
        self._agenda.clear()
        # # 1
        if not self._profile:
            self._profile = user_profile

        # We save user goals for handling requests from system. Agenda will be built using user_goals.
        if not self._user_goals:
            self._user_goals = user_goals 

        # 2
        # all_intentions_in_scenario = self.user_goals.keys()
        all_intentions_in_scenario = ['booking']

        # 3
        # self._agenda_dict = {intent:Agenda() for intent in all_intentions_in_scenario}

        # 4
        # self._intent_to_domain = {}
        # for intent in all_intentions_in_scenario:
        #     for _,domain in domain_dict.items():
        #         if intent in domain.intentions:
        #             self._intent_to_domain[intent] = domain
        # 5
        # for intent,domain in self._intent_to_domain.items():
        #     # choose agenda goal_slots for a specific intent
        #     selected_goal_slots = self._choose_agenda_slots(scenario,intent,domain) 
        #     # create user agenda
        #     self.create_agenda(selected_goal_slots,intent,domain)
        #5 create agenda
        # choose agenda goal_slots for a specific intent
        domain, intent = 'movie', 'booking'
        selected_goal_slots = self._choose_agenda_slots(self._user_goals,intent,domain) 
        self.create_agenda(selected_goal_slots,intent,domain)

    def start_conversation(self):
        """
        Start the conversation! This function is mainly used to start the conversation with the system.

        Returns:
            list[Annotation]
        
        The following steps take place when starting a conversation:
            1- User updates his current intent and sets his current Agenda based on the intent.
            2- Based on politeness of user (see tests/files/sample_user_profile.txt) greetes the system.
              Also, user may not express his intetion when starting the conversation (for example he may only
              say Hi!) which we control using expresses_intention_with_greeting characteristic of the user.
            3- 
        """
        response_list = []

        # 1
        # self._update_user_intent()
        # get current agenda
        # current_agenda = self._agenda_dict[self._current_intent]
        current_agenda = self._agenda

        # 2
        # add greeting() act to agenda if user is polite!
        if get_random_number() < self._profile["polite"]:
            # user can express intention with greeting
            response_list += [Annotation(diagact=Greeting,intent='booking',domain='movie',goal_list=None)]
            # if get_random_number() < self._profile["expresses_intention_with_greeting"]:
            #     response_list += [Annotation(diagact=Greeting(),intent=self._current_intent)]
            # else:
            #     response_list += [Annotation(diagact=Greeting())]
        
        num_items = self.number_of_items_to_pop_based_on_profile(self._agenda)
        logger.debug("created {} to pop from agenda for starting the conversation\n".format(num_items))

        # pop num_items annotatios from agenda as long as they are of type "INFORM"
        while num_items:
            annot = current_agenda[-1]
            if annot.diagact.name == 'INFORM':
                response_list.append(annot)
                current_agenda.pop()
                num_items -= 1
            else:
                break  
        
        # pop some inform diagacts
        # if get_random_number() < 

        # return merge_annotations_with_similar_diagacts(response_list)
        return response_list

    def number_of_items_to_pop_based_on_profile(self,agenda):
        return max(1,int(self._profile["verbose"]*len(agenda)))

    def create_agenda(self, selected_goal_slots_with_intents, intent, domain):        
        # add inform() and request() acts to agenda based on user "informed" characteristic
        inform_slot_list,request_slot_list = [],[]
        # make sure there is at least one inform annotation in the agenda
        atleast_one_inform_in_agenda = False
        for intent,goal in selected_goal_slots_with_intents:

            # if domain.is_slot_required(intent,gs.name):
            if not goal.type=='open':
                inform_slot_list.append(Annotation(diagact=Inform,goal_list=[copy.deepcopy(goal)],intent=intent,domain=domain))
                atleast_one_inform_in_agenda = True
            # only required slots with is_open flag
            else:
                rand = get_random_number()
                if not atleast_one_inform_in_agenda:
                    rand = 0.0
                if rand < self._profile["inform"]:
                    inform_slot_list.append(Annotation(diagact=Inform,goal_list=[copy.deepcopy(goal)], intent=intent,domain=domain))
                    atleast_one_inform_in_agenda = True
                else:
                    request_slot_list.append(Annotation(diagact=Request,goal_list=[Goal(slot=goal.slot,value=None,type=None)],
                    intent=intent,domain=domain))

            # # optioanl slots
            # else:
            #     request_slot_list.append(Annotation(diagact=Request(),\
            #     goal_slot_list=[GoalSlot(slot_name=gs.name)],intent=intent))
            #     # TODO: Should we set user_goal value of slot to None?!
            #     # update user_goals and make the value for gs set to []
            #     # self.user_goals[intent][gs.name].value = []


        
        self._agenda.push(request_slot_list)
        self._agenda.push(inform_slot_list)

        
        logger.info("Agenda was successfully created for intent {}!\n Agenda=\n {}".\
            format(intent,self._agenda))


    def _choose_agenda_slots(self,user_goals,intent,domain):
        """
        Choose agenda slots for a specific intention.
        All required slots are in scenario but not all required slots should appear in agenda
        """
        # all_goals_and_slots = []
        # for _,ug in scenario.user_goals:
        #     for gs in ug.goal_slots:
        #         # only select goal slot that correspond to the given intent
        #         if ug.intent == intent:
        #             all_goals_and_slots.append((ug.intent,gs))

        selected_goal_slots_with_intents = []
        for ind, goal in enumerate(user_goals.goal_list):
            if ind==0:
                # make sure there is at least one chosen!
                rand = 0.0
            else:
                rand = get_random_number()
            if rand < self._profile["agenda_size"]:
                # if not domain.is_slot_required(intent,gs.name):
                #     # optional slots are not always chosen! (user maybe is too picky)
                #     if get_random_number() < self._profile["asks_about_optional_slots"]:
                #         selected_goal_slots_with_intents.append((intent,gs))
                # # choose the required slot
                # else:
                selected_goal_slots_with_intents.append((intent,goal))
        
        return selected_goal_slots_with_intents
    

    def next(self,sys_annotaions,turn_count):
        """
        Generate next User Action based on last System Action
        Args:
            sys_annotations: list of system annotations
            turn_count (int): current turn in the conversation
        Returns:
            user_annotations: list of annotations returned from user
            episode_over: flag to end the conversation
        """
        episode_over = False
        failed = False
        user_response = []
        user_annoations = []

        # Check whether to end the conversation or not
        # is max turn reached?
        if self._max_turn > 0 and turn_count >= self._max_turn-1:
            episode_over = True

        else:
            for sys_annotation in sys_annotaions:
                sys_act = sys_annotation.diagact
                if sys_act.name == "GREETING":
                    print(sys_annotaions)
                    user_annoations += self.start_conversation()
                elif sys_act.name == "INFORM":
                    user_annoations += self.response_to_inform(sys_annotation)
                elif sys_act.name == "REQUEST":
                    user_annoations += self.response_to_request(sys_annotation)
                elif sys_act.name == "CONFIRM":
                    user_annoations += self.response_to_confirm(sys_annotation)
                elif sys_act.name == "OFFER":
                    user_annoations += self.response_to_offer(sys_annotation)
                elif sys_act.name == "SELECT":
                    user_annoations += self.response_to_select(sys_annotation)
                elif sys_act.name == "AFFIRM":
                    # TODO: How to response to system AFFIRM ?!
                    user_annoations = []
                elif sys_act.name == "NEGATE":
                    user_annoations += self.response_to_negate(sys_annotation)
                elif sys_act.name == "GOOD_BYE":
                    episode_over = True
                elif sys_act.name == "ACKNOWLEDGE":
                    # Ignore System Acknowlegement
                    user_annoations = []
                elif sys_act.name == "NOTIFY_SUCCESS":
                    user_annoations += self.response_to_notifysuccess(sys_annotation)
                    episode_over = True
                elif sys_act.name == "NOTIFY_FAILURE":
                    user_annoations += self.response_to_notifyfailure(sys_annotation)
                    episode_over = True
                    failed = True
                
            # Break user annotation into single GoalSlot annotations and  add them to agenda
            self.update_agenda(self._break_annotations(user_annoations),self._agenda)
            # print(self._agenda)
            
            # pop user response from agenda if episode is not over
            if not episode_over:
                # user_response = self.current_agenda.pop(number_of_items=len(user_annoations),
                                                        # multi_diagact=False)
                # self._update_user_intent()
                
                user_response += self._agenda.pop(
                    number_of_items=
                    self.number_of_items_to_pop_based_on_profile(self.current_agenda),
                    multi_diagact=False)
                
                # user_response = merge_annotations_with_similar_diagacts(user_response)
            
            # if user_response is empty then terminate episode
            if not user_response:
                print("USER RESPNSE IS EMPTY")
                episode_over = True
                if get_random_number() < self._profile["polite"]:
                    user_response = [Annotation(diagact=GoodBye,intent='booking',domain='movie',goal_list=None)]

                logger.debug("Agenda is empty now. Setting episove_over to True to end the conversation!")
            
        return user_response,episode_over, failed    


    # def _update_user_intent(self):
        
    #     all_intentions_in_agenda_list = list(self._agenda_dict.keys())
    #     # if current_intent is not set randmly pick one
    #     if not self._current_intent or self._current_intent not in all_intentions_in_agenda_list:
    #         self._current_intent = pick_random(all_intentions_in_agenda_list)[0]
    #         logger.debug("User intention set to {}".format(self._current_intent))
        
    #     # if only one intention is available then skip the rest of the fucntion
    #     if len(all_intentions_in_agenda_list)==1:
    #         return
        
    #     #TODO: change current_intent based on user behaviour (This needs to be implemented carefully)
    #     # should we consider order of intents when switching ?
    #     if get_random_number() < self._profile["periodically_changes_intent"]:
    #         prev_intent = self._current_intent
    #         all_intentions_in_agenda_list.remove(prev_intent)
    #         self._current_intent = pick_random(all_intentions_in_agenda_list)[0]


    def update_agenda(self,annotation_list,agenda):
        sorted_annotation = sorted(annotation_list,key=lambda a:-a.diagact.priority)
        agenda.push(sorted_annotation)

    def _break_annotations(self,annotation_list):
        """
        Break annotation_list into list of annotations with single GoalSlot
        (User agenda should have annotations with only one GoalSlot ease duplicate removal)
        """
        single_slot_annotations = []
        # print(annotation_list)
        for annot in annotation_list:                
            if annot.goal_list and len(annot.goal_list)>1:
                for gs in annot.goal_list:
                    single_slot_annotations.append(Annotation(diagact=annot.diagact,goal_list=[gs],intent=annot.intent,domain='movie'))
            else:
                single_slot_annotations.append(annot)

        return single_slot_annotations

    @property
    def max_turn(self):
        return self._max_turn

    @property
    def profile(self):
        return self._profile
    
    @property
    def user_goals(self):
        return self._user_goals

    @property
    def agenda_dict(self):
        return self._agenda_dict
    
    @property
    def current_agenda(self):
        # return self._agenda_dict[self._current_intent]
        return self._agenda
    
    def __str__(self):
        s = "AGENDA BASED USER WITH:\n"
        s += "User bot name is {}\n\n".format(self.name)
        s += "max turn is {}\n\n".format(self.max_turn)
        s += "Profile is: {}\n\n".format(self.profile)
        s += "Agenda is:\n {}\n\n".format(self.agenda)
        return s
       

    def response_to_inform(self,sys_annotaion):
        """
        Reply to system inform. User can modify some of the previously informed values

        Args:
            - sys_annotaion (Annotation): System annotation 
        Returns:
            - list[Annotation]
        """

        # TODO: user can modify some of the previously informed values
        return []
    

    def response_to_request(self,sys_annotaion):
        """
        Reply to system request. This could be either inform or request_options

        Args:
            - sys_annotaion (Annotation): System annotation 
        Returns:
            - list[Annotation]
        """
        # print('IN RESPONSE REQUESTR MODE')
        # print(sys_annotaion)

        response_list = []
        intent = sys_annotaion.intent
        user_goal = self._user_goals
        # print(user_goal)
        # domain = self._intent_to_domain[self._current_intent]
        requested_slots = sys_annotaion.goal_list
        goal_slots_to_inform = []
        goal_slots_to_request_option = []
        for rs in requested_slots:
            slot_name = rs.slot
            
            # pass if slot is already informed
            if slot_name in self._informed_slots:
                continue
        
            # find user goal with that slot
            user_goal_for_slot = None
            for g in user_goal.goal_list:
                if g.slot==slot_name:
                    user_goal_for_slot = g
         
            # If user does not care about the slot; then either inform the system or request for options
            if user_goal_for_slot.value== ['dont care']:
                if get_random_number() < self._profile["requests_for_options"]:
                    # make sure slot is not already asked for ReqOpt
                    if slot_name not in self._request_option_slots:
                        goal_slots_to_request_option.append(copy.deepcopy(user_goal[slot_name]))
                else:
                    goal_slots_to_inform.append(copy.deepcopy(user_goal_for_slot))
            else:
                goal_slots_to_inform.append(copy.deepcopy(user_goal_for_slot))
                self._informed_slots.add(slot_name)
                

        if goal_slots_to_inform:
            response_list.append(Annotation(diagact=Inform,goal_list=goal_slots_to_inform,intent=intent,domain='movie'))
        
        if goal_slots_to_request_option:
            response_list.append(Annotation(diagact=RequestOptions(),goal_slot_list=goal_slots_to_request_option,intent=intent))
            for req_opt_goal_slot in goal_slots_to_request_option:
                self._request_option_slots.add(req_opt_goal_slot.name)
            
            # It is possible that we have already added INFROM annotations with current slot_name
            # to agenda. Make sure to remove them since we are requesting optios for those slots
            to_be_removed_annotations_index = []
            for req_opt_goal_slot in goal_slots_to_request_option:
                to_be_removed_annotations_index += self.current_agenda.search_agenda("INFORM",
                                                                        goal_slot_name=req_opt_goal_slot.name) 
            self.current_agenda.remove_by_index(to_be_removed_annotations_index)

        # print(response_list)

        return response_list
    

    def response_to_confirm(self,sys_annotaion):
        """
        Respond to system confirm annotation
        Args:
            - sys_annotaion (Annotation): System annotation 
        Returns:
            - list[Annotation]
        """
        # get user_goals (what current scenario says about user goals in this outline)
        intent = sys_annotaion.intent
        user_goal = self._user_goals
        response_list = []
        negation_list = []
        # for goal in sys_annotaion.goal_list:
        #     user_prefered_goal_slot = copy.deepcopy(user_goal[gs.name])
        #     if gs!=user_prefered_goal_slot:
        #         negation_list.append(user_prefered_goal_slot)
        if negation_list:
            response_list.append(Annotation(diagact=Negate(),goal_slot_list=negation_list,intent=intent))
        else:
            response_list.append(Annotation(diagact=Affirm,intent=intent,domain='movie',goal_list=None))

        return response_list


    def response_to_offer(self,sys_annotaion):
        """
        Response to system offer
        Args:
            - sys_annotaion (Annotation): System annotation 
        Returns:
            - list[Annotation]
        """
        response_list = []
        intent = sys_annotaion.intent

        # merge goal slots with same slot_name
        merged_goal_slots = merge_goal_slots_with_similar_slot_name(sys_annotaion.goal_slot_list)

        # iterate through GoalSlot list to check what to do for each offered slot in sys_annotation
        for gs in merged_goal_slots:
            slot_name,slot_offered_values_set = gs.name,set(gs.value)
            
            # get the GoalSlot info from user_goal
            user_goal_slot = self.user_goals[intent][slot_name]
            
            # decide what to do next based on slot_value and slot_flag (user side)
            user_goal_slot_values_set,user_goal_slot_flag = set(user_goal_slot.value),user_goal_slot.flag
            if user_goal_slot_flag==GOAL_SLOT_FLAGS.is_fixed:
                # if user_goal_slot_values not in slot_offered_values then negate
                if not user_goal_slot_values_set.issubset(slot_offered_values_set):
                    response_list.append(Annotation(diagact=Negate(),intent=intent))
                else:
                    response_list.append(Annotation(diagact=Affirm(),intent=intent))
            
            elif user_goal_slot_flag==GOAL_SLOT_FLAGS.is_flexible:
                # if user_goal_slot_values not in slot_offered_values then RequestAlternatives else Affirm
                if not user_goal_slot_values_set.issubset(slot_offered_values_set):
                    response_list.append(Annotation(diagact=RequestAlternatives(),intent=intent))
                else:
                    response_list.append(Annotation(diagact=Affirm(),intent=intent))
            
            elif user_goal_slot_flag==GOAL_SLOT_FLAGS.is_multiple:
                # if any of user_goal_slot_values in slot_offered_values then Affirm else Negate
                should_affirm = any(True if x in slot_offered_values_set else\
                    False for x in user_goal_slot_values_set)
                if should_affirm:
                    response_list.append(Annotation(diagact=Affirm(),intent=intent))
                else:
                    response_list.append(Annotation(diagact=Negate(),intent=intent))
            
            elif user_goal_slot_flag==GOAL_SLOT_FLAGS.is_open:
                # Always Affirm!
                response_list.append(Annotation(diagact=Affirm(),intent=intent))

        return response_list


    def response_to_select(self,sys_annotaion):
        """
        [summary]
        
        Args:
            sys_annotaion ([type]): [description]
        
        Returns:
            [type]: [description]
        """

        response_list = []
        intent = sys_annotaion.intent
        goal_list = sys_annotaion.goal_list
        
        response_list.append(Annotation(diagact=Inform, goal_list=goal_list,intent=intent,domain='movie'))

        return response_list
        # merge goal slots with same slot_name
        # merged_goal_slots = merge_goal_slots_with_similar_slot_name(sys_annotaion.goal_slot_list)
        
        # iterate through GoalSlot list to check what to do for each selected slot in sys_annotation
        for gs in merged_goal_slots:
            slot_name,slot_selected_values_set = gs.name,set(gs.value)
        
            # get the GoalSlot info from user_goal
            user_goal_slot = self.user_goals[intent][slot_name]
        
            # decide what to do next based on slot_value and slot_flag (user side)
            user_goal_slot_values_set,user_goal_slot_flag = set(user_goal_slot.value),user_goal_slot.flag
            if user_goal_slot_flag in [GOAL_SLOT_FLAGS.is_fixed,GOAL_SLOT_FLAGS.is_flexible]:
                # if user_goal_slot_values not in slot_offered_values then RequestAlternatives else Inform
                if not user_goal_slot_values_set.issubset(slot_selected_values_set):
                    response_list.append(Annotation(diagact=RequestAlternatives(),intent=intent))
                else:
                    response_list.append(Annotation(diagact=Inform(),\
                    goal_slot_list=[GoalSlot(slot_name,list(user_goal_slot_values_set),user_goal_slot_flag)],\
                    intent=intent))
        
            elif user_goal_slot_flag==GOAL_SLOT_FLAGS.is_multiple:
                # check for all slot_names in slot_selected_values_set and randomly choose one, if set is empty
                # then RequestAlternatives
                all_slots_in_selected_slots = user_goal_slot_values_set.intersection(slot_selected_values_set)
                if not all_slots_in_selected_slots:
                    response_list.append(Annotation(diagact=RequestAlternatives(),intent=intent))
                else:
                    chosen_slot_name = pick_random(list(all_slots_in_selected_slots))[0]
                    response_list.append(Annotation(diagact=Inform(),\
                    goal_slot_list=[GoalSlot(slot_name,[chosen_slot_name],user_goal_slot_flag)],\
                    intent=intent))           
        
            elif user_goal_slot_flag==GOAL_SLOT_FLAGS.is_open:
                # randomly choose one slot
                chosen_slot_name = pick_random(list(slot_selected_values_set))[0]
                response_list.append(Annotation(diagact=Inform(),\
                    goal_slot_list=[GoalSlot(slot_name,[chosen_slot_name],user_goal_slot_flag)],\
                intent=intent))           

        return response_list


    def response_to_negate(self,sys_annotation):
        """
        Respond to negation from system.
        System Negates user in these scenarios:
            1- In response to user CONFIRMing a slot value, system negates that value
            2-  
        Args:
            - sys_annotaion (Annotation): System annotation 
        Returns:
            - list[Annotation]
        """
        pass

    def response_to_notifysuccess(self,sys_annotaion):
        """
        Respond to notify_success annotation from the system
        """
        # TODO: Note that we currrently handle one annotation sent from the user! (Mansour)
        response_list = []
        intent = sys_annotaion.intent
        response_list.append(Annotation(diagact=ThankYou,intent=intent,domain='movie',goal_list=None))
        
        return response_list

    def response_to_notifyfailure(self,sys_annotaion):
        """
        Respond to notify_failure annotation from the user
        """
        # TODO: if notify_failure has goal_list then it means system could not found values for those slots
        # and user should act based on user_goal
        intent = sys_annotaion.intent
        response_list = [Annotation(diagact=GoodBye,intent=intent,domain='movie',goal_list=None)]
        
        return response_list





# def merge_annotations_with_similar_diagacts(annotation_list):

# 	# from chat.outline.annotation import Annotation
# 	# diagact_to_intent_to_gs: {diagact:{intent:goal_slot_list}}
# 	diagact_to_intent_to_gs = {} 
# 	for annotation in annotation_list:
# 		diagact = annotation.diagact
# 		intent = annotation.intent
# 		if diagact not in diagact_to_intent_to_gs:
# 			diagact_to_intent_to_gs[diagact] = {}
# 			diagact_to_intent_to_gs[diagact][intent] = list(annotation.goal_slot_list)
# 		else:
# 			if intent not in diagact_to_intent_to_gs[diagact]:
# 				diagact_to_intent_to_gs[diagact][intent] = annotation.goal_slot_list
# 			else:    
# 				diagact_to_intent_to_gs[diagact][intent] += annotation.goal_slot_list

# 	merged_annotations = []
# 	for diagact, intent_to_gs_list in diagact_to_intent_to_gs.items():
# 		for intent, gs_list in intent_to_gs_list.items():
# 			merged_annotations.append(Annotation(diagact = diagact(), goal_slot_list = gs_list, intent = intent))
# 	# sort annotations based on diagact priority
# 	sorted_annotations = sorted(merged_annotations, key = lambda annot:annot.diagact.priority, reverse = True)
# 	return sorted_annotations



