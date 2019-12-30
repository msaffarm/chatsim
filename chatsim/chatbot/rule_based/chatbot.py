

entities = ['date', 'time', 'movie', 'ticket', 'theater']


class ChatBot():

    def __init__(self):
        self.asked_entities = set()

    def get_response(self, input_text):

        if 'date' in input_text:
            self.asked_entities.add('date')
        if 'time' in input_text:
            self.asked_entities.add('time')
        if 'movie' in input_text:
            self.asked_entities.add('movie')
        if 'people' in input_text:
            self.asked_entities.add('ticket')
        if 'theater' in input_text:
            self.asked_entities.add('theater')

        for ent in entities:
            if ent not in self.asked_entities:
                if ent == 'date':
                    return 'what date ?'
                if ent == 'time':
                    return 'what time ?'
                if ent == 'movie':
                    return 'what is the movie ?'
                if ent == 'ticket':
                    return 'how many people ?'
                if ent == 'theater':
                    return 'which theater ?'

        if 'yes' in input_text or 'that is right' in input_text:
            return 'purchase confirmed successfully made'

        if len(self.asked_entities) == 5:
            return 'Do you confirm ?'
