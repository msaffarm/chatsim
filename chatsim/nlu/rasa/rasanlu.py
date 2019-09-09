import logging
import os
from pathlib import Path, PosixPath
from typing import Dict, List
from chatsim.utils import Annotation, DiagAct, Goal, UserGoal, read_user_profile
from chatsim.utils.diagact import *

import requests
import json

import yaml

from rasa_nlu import config
from rasa_nlu.model import Interpreter, Trainer
from rasa_nlu.training_data import load_data

from chatsim.utils import DATA_DIR

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CURRENT_DIR = Path(os.path.dirname(__file__))
DEFAULT_RASA_NLU = CURRENT_DIR / 'rasa_nlu_config.yml'
RASA_NLU_PIPELINE_DEFAULT_PATH = CURRENT_DIR / 'rasa_nlu_pipeline_configs'
MODELS_DIR = CURRENT_DIR / 'trained_models'

class RasaNLU(object):

    def __init__(self):
        self.interpreter = None

    def run(self, config_path: [str, PosixPath] = DEFAULT_RASA_NLU):
        # read the config file
        rasa_config = self.read_config(config_path)

        # # prepare training data
        # if rasa_config['data']['type'] == 'csv':
        #     temp_training_data = training_data = convert_nlu_data_to_rasa_format(DATA_DIR /
        #                                                                          rasa_config['data']['file_name'])
        #     # persist data
        #     filename = DATA_DIR / str(rasa_config['data']['file_name'] + '.json')
        #     persist_rasa_data(temp_training_data, filename)
        filename = DATA_DIR / str(rasa_config['data']['file_name'])
        # if model does not exist then train it
        project_path = MODELS_DIR / rasa_config['trainer']['project_name']
        model_name = project_path / rasa_config['trainer']['config_name']
        if not model_name.exists():
            training_data = load_data(filename.absolute().as_posix())
            # train the model with given config and persist
            model_directory = self.train_model(rasa_config, training_data)

        # create an interpreter for inference
        self.interpreter = Interpreter.load(model_name.absolute().as_posix())
        logger.info('Created interpreter with the trained model! Ready of inference!')

    def train_model(self, rasa_config: Dict, training_data):
        # load config
        trainer_config_path = RASA_NLU_PIPELINE_DEFAULT_PATH / rasa_config['trainer']['config_name']
        trainer_config = config.load(trainer_config_path)

        # train model
        trainer = Trainer(trainer_config)
        logger.info('Training the model!')

        self.trained_model = trainer.train(training_data)
        logger.info('Persisting model')
        
        project_name = rasa_config['trainer']['project_name']
        model_name = rasa_config['trainer']['config_name']
        model_directory = trainer.persist(MODELS_DIR.absolute().as_posix(),project_name=project_name,fixed_model_name=model_name)
        logger.info('Persisted model!')

        return model_directory

    def get_intent(self, input_text: str) -> str:
        return self.get_nlu_response(input_text)['intent']

    def get_entities(self, input_text: str) -> List:
        return self.get_nlu_response(input_text)['entities']

    # def get_nlu_response(self, input_text: str) -> Dict:
    #     response = self.interpreter.parse(input_text)

    #     return response

    def create_interpreter(self, model_dir: str):
        self.interpreter = Interpreter.load(model_dir)
        logger.info('Created interpreter with the trained model! Ready of inference!')


    def read_config(self, config_path: [str, PosixPath]) -> Dict:
        with open(config_path, 'r') as stream:
            try:
                config = yaml.load(stream)
            except yaml.YAMLError as exc:
                logger.error(exc)

        return config
    
    def get_server_response(self, input_text: str, project_name: str, model_name: str, port: int = 5000) -> Dict:
        url = f'http://127.0.0.1:{port}/parse'
        data = {
            "q":input_text, 
            "project":project_name,
            "model":model_name
        }
        response = requests.post(url, data=json.dumps(data))
        json_data = json.loads(response.text)

        # add entities if dialgoue action is of type REQUEST
        if json_data['intent']['name'] == 'REQUEST':
            if ('date' in input_text) or ('day' in input_text):
                json_data['entities'].append(
                    {
                        'entity': 'date',
                        'value': None
                    }
                    )
            if ('time' in input_text) or ('when' in input_text) or ('showtime' in input_text):
                json_data['entities'].append(
                    {
                        'entity': 'time',
                        'value': None
                    }
                    )
            if ('how many people' in input_text) or ('people' in input_text) or ('tickets' in input_text) or ('many' in input_text):
                json_data['entities'].append(
                    {
                        'entity': 'num_people',
                        'value': None
                    }
                )
            if ('theater' in input_text) or ('theatre' in input_text):
                json_data['entities'].append(
                    {
                        'entity': 'theatre_name',
                        'value': None
                    }
                )
            if ('movie' in input_text):
                json_data['entities'].append(
                    {
                        'entity': 'movie',
                        'value': None
                    }
                )

        return json_data
    
        



def main():
    rasa = RasaNLU()
    rasa.run()
    print(rasa.get_nlu_response('what time?'))


if __name__ == "__main__":
    main()
