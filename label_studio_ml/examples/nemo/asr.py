import os
import logging
import nemo
import nemo.collections.asr as nemo_asr

from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import DATA_UNDEFINED_NAME


logger = logging.getLogger(__name__)


class NemoASR(LabelStudioMLBase):

    def __init__(self, model_name='stt_hi_conformer_ctc_medium', **kwargs):
        super(NemoASR, self).__init__(**kwargs)

        # Find TextArea control tag and bind ASR model to it
        self.from_name, self.to_name, self.value = self._bind_to_textarea()

        # This line will download pre-trained QuartzNet15x5 model from NVIDIA's NGC cloud and instantiate it for you
        self.model = nemo_asr.models.EncDecCTCModel.from_pretrained(model_name=model_name)

    def predict(self, tasks, **kwargs):
        output = []
        audio_paths = []
        for task in tasks:
            audio_url = task['data'].get(self.value) or task['data'].get(DATA_UNDEFINED_NAME)
            audio_path = self.get_local_path(audio_url)
            audio_paths.append(audio_path)

        # run ASR
        transcriptions = self.model.transcribe(paths2audio_files=audio_paths)

        for transcription in transcriptions:
            output.append({
                'result': [{
                    'from_name': self.from_name,
                    'to_name': self.to_name,
                    'type': 'textarea',
                    'value': {
                        'text': [transcription]
                    }
                }],
                'score': 1.0
            })
        return output

    def _bind_to_textarea(self):
        from_name, to_name, value = None, None, None
        for tag_name, tag_info in self.parsed_label_config.items():
            if tag_info['type'] == 'TextArea':
                from_name = tag_name
                if len(tag_info['inputs']) > 1:
                    logger.warning(
                        'ASR model works with single Audio or AudioPlus input, '
                        'but {0} found: {1}. We\'ll use only the first one'.format(
                            len(tag_info['inputs']), ', '.join(tag_info['to_name'])))
                if tag_info['inputs'][0]['type'] not in ('Audio', 'AudioPlus'):
                    raise ValueError('{0} tag expected to be of type Audio or AudioPlus, but type {1} found'.format(
                        tag_info['to_name'][0], tag_info['inputs'][0]['type']))
                to_name = tag_info['to_name'][0]
                value = tag_info['inputs'][0]['value']
        if from_name is None:
            raise ValueError('ASR model expects <TextArea> tag to be presented in a label config.')
        return from_name, to_name, value
