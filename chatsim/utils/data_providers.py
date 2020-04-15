import logging
import json
from collections import OrderedDict, Counter

from chatsim.utils import DATA_DIR

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GoogleDataReader(object):

    def __init__(self, path_list=None):
        self._data = []
        if path_list:
            for path in path_list:
                self._data += self.read_json_file(path)

        self.meta = {}
        self.meta["user_intents"] = Counter()
        self._user_intents = Counter()
        self._sys_intents = Counter()
        self._solo_intent = 0

    @staticmethod
    def read_json_file(path):
        return json.load(open(path))

    @property
    def data(self):
        return self._data

    def read_data_from(self, file_path):
        self._data = self.read_json_file(file_path)

    def create_rasa_nlu_dict(self):
        exmaples = []
        for turn in self.turn_iter():
            if "user_acts" in turn:
                if self._is_rasa_nlu_compatible(turn, "user"):
                    exmaples.append(self._create_rasa_nlu_example(turn, sytem_or_user="user"))
            if "system_acts" in turn:
                if self._is_rasa_nlu_compatible(turn, "system"):
                    exmaples.append(self._create_rasa_nlu_example(turn, sytem_or_user="system"))

        return exmaples

    def _create_rasa_nlu_example(self, turn, sytem_or_user="user"):
        example = OrderedDict()
        if sytem_or_user == "user":
            utter, act = turn["user_utterance"], turn["user_acts"]
        elif sytem_or_user == "system":
            utter, act = turn["system_utterance"], turn["system_acts"]
        example["text"] = utter["text"]
        example["intent"] = act[0]["type"]
        # adding entities
        entities = []
        text = utter["text"]
        tokens = utter["tokens"]
        for slot in utter["slots"]:
            entity = OrderedDict()

            # convert indices!!!
            slot_tokens = tokens[slot["start"]:slot["exclusive_end"]]
            start = text.find(slot_tokens[0])
            end = text.find(slot_tokens[-1]) + len(slot_tokens[-1])
            entity["start"] = start
            entity["end"] = end
            entity["value"] = text[start:end]
            entity["entity"] = slot["slot"]
            entities.append(entity)

        example["entities"] = entities
        return example

    def get_intents(self):
        for turn in self.turn_iter():
            if "user_acts" in turn:
                for ua in turn["user_acts"]:
                    self._user_intents.update({ua["type"]: 1})
                if len(ua) == 1:
                    self._solo_intent += 1
            if "system_acts" in turn:
                for ua in turn["system_acts"]:
                    self._sys_intents.update({ua["type"]: 1})
        return "User acts:\n {}\n\n System acts:\n {} with {} solo intents".format(self._user_intents,
                                                                                   self._sys_intents,
                                                                                   self._solo_intent)

    def _get_slot_value_map(self, utter):
        svmap = OrderedDict()
        tokens = utter["tokens"]
        for slot in utter["slots"]:
            val = " ".join(tokens[slot["start"]:slot["exclusive_end"]])
            svmap[slot["slot"]] = val
        return svmap

    def diag_iter(self):
        for dialogue in self.data:
            yield dialogue

    def turn_iter(self):
        for dialogue in self.data:
            for turn in dialogue["turns"]:
                yield turn

    def _is_rasa_nlu_compatible(self, turn, speaker):
        is_compatible = True
        if speaker == "user" or speaker == 'system':
            type_set = set([t["type"] for t in turn["user_acts"]])
            if len(type_set) < 1:
                is_compatible = False
        # else:
        #     type_set = set([t["type"] for t in turn["system_acts"]])
        #     if type_set!=set(["REQUEST"]):
        #         is_compatible = False

        return is_compatible

    def stats(self):
        nlu_turns, num_turns = 0,0
        for turn in self.turn_iter():
            num_turns += 1
            if self._is_rasa_nlu_compatible(turn, speaker="user"):
                nlu_turns += 1
        result = "Totol turns={} with {} nlu compatible turns".format(num_turns, nlu_turns)
        return result

    def __str__(self):
        return self.stats()

    def nlu_to_json(self, nlu_data, path):
        rasa_nlu_data = OrderedDict()
        rasa_nlu_data["rasa_nlu_data"] = dict(common_examples=nlu_data, entity_examples=[], intent_examples=[])
        res = json.dumps(rasa_nlu_data, indent=2)
        with open(path, 'w') as f:
            f.write(res)


def main():
    dr = GoogleDataReader()
    dr.read_data_from(DATA_DIR / 'sim-M/dev.json')
    dev_data = dr.create_rasa_nlu_dict()

    dr.read_data_from(DATA_DIR / 'sim-M/test.json')
    test_data = dr.create_rasa_nlu_dict()

    dr.read_data_from(DATA_DIR / 'sim-M/train.json')
    train_data = dr.create_rasa_nlu_dict()

    dr.nlu_to_json(dev_data + test_data + train_data, DATA_DIR / 'compiled/sim-M-complete.json')


if __name__ == "__main__":
    main()
