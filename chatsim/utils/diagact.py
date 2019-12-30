from chatsim.utils import DiagAct

# a list of common diag acts in task-oriented conversation (based on https://arxiv.org/pdf/1801.04871.pdf)

Greeting = DiagAct(name='GREETING', priority=4)
Inform = DiagAct(name='INFORM', priority=3)
Request = DiagAct(name='REQUEST', priority=1)
Confirm = DiagAct(name='CONFIRM', priority=1)
RequestAlts = DiagAct(name='REQUEST_ALTS', priority=1)
Offer = DiagAct(name='OFFER', priority=1)
Select = DiagAct(name='SELECT', priority=1)
Affirm = DiagAct(name='AFFIRM', priority=2)
Negate = DiagAct(name='Negate', priority=2)
NotifySuccess = DiagAct(name='NOTIFY_SUCCESS', priority=2)
NotifyFailure = DiagAct(name='NOTIFY_FAILURE', priority=2)
ThankYou = DiagAct(name='THANK_YOU', priority=1)
GoodBye = DiagAct(name='GOODBYE', priority=2)
CantUnderstand = DiagAct(name='CANT_UNDERSTAND', priority=2)
Other = DiagAct(name='Other', priority=2)

__all__ = ['Greeting', 'Inform', 'Request', 'Confirm', 'RequestAlts', 'Offer', 'Select', 'Affirm', 'GoodBye',
           'NotifySuccess', 'NotifyFailure', 'ThankYou', 'Other', 'Negate']
