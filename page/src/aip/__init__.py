# -*- coding: utf-8 -*-
"""
    aip public
"""

from .ocr import AipOcr
from .nlp import AipNlp
from .face import AipFace
from .imagecensor import AipImageCensor
from .imagecensor import AipImageCensor as AipContentCensor
from .kg import AipKg
from .speech import AipSpeech
from .imageclassify import AipImageClassify
from .imagesearch import AipImageSearch
from .bodyanalysis import AipBodyAnalysis
from .imageprocess import AipImageProcess
from .easydl import EasyDL

# 百度 AI 应用
BAIDU_API_INFO = {
    "appId": "11307942",
    "apiKey": "A0sgOudHqBipVotebf7K1i08",
    "secretKey": "EYG0CjQofDrtPb5VcA8lgWCu1dUTWLoW"
}

BAIDU_TOKEN_URL ='https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=A0sgOudHqBipVotebf7K1i08&client_secret=EYG0CjQofDrtPb5VcA8lgWCu1dUTWLoW'
BAIDU_NLP_URL = 'https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify?charset=UTF-8&access_token={}'