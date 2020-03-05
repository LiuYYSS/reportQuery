import io
import json
import os
import sys
from simpletransformers.question_answering import QuestionAnsweringModel
import platform
import requests
import pdf2image as pdf2image


def to_list(tensor):
    return tensor.detach().cpu().tolist()


endpoint = 'https://uksouth.api.cognitive.microsoft.com/'
ocr_url = 'https://uksouth.api.cognitive.microsoft.com/vision/v2.1/ocr'
subscription_key = 'ffcc4bbd174c4b6e97d0a945aebf8b98'

inputPath = input("PDF Path:")
print("PDF path:", inputPath)

print("starts converting PDF to image, please wait")
pages = None
if os.path.isfile(inputPath):
    if platform.system() == 'Windows':
        pathname = os.path.dirname(sys.argv[0])
        pathname = os.path.abspath(pathname) + os.path.sep + "poppler_win" + os.path.sep + "bin"
        pages = pdf2image.convert_from_path(inputPath, 200, poppler_path=pathname, fmt="jpeg")
    else:
        pages = pdf2image.convert_from_path(inputPath, 200, fmt="jpeg")
else:
    print("input file doesn't exist")
    exit()


outputString = ""
pageNum = 0
while pageNum < len(pages):
    print(pageNum)
    imgByteArr = io.BytesIO()
    pages[pageNum].save(imgByteArr, format=pages[pageNum].format)
    imgByteArr = imgByteArr.getvalue()
    headers = {'Ocp-Apim-Subscription-Key': subscription_key, 'Content-Type': 'application/octet-stream'}
    params = {'language': 'unk', 'detectOrientation': 'true'}
    response = requests.post(ocr_url, headers=headers, params=params, data=imgByteArr)
    response.raise_for_status()
    ocrResult = response.json()
    ocrResult = json.dumps(eval(str(ocrResult)))

    resultJSONObject = json.loads(ocrResult)
    regions = resultJSONObject['regions']
    for region in regions:
        lines = region['lines']

        for line in lines:
            words = line['words']
            for word in words:
                text = word.get('text')
                outputString += text + " "
    pageNum +=1
print(outputString)

while(True):
    question = input("question:")
    to_predict = [{'context': outputString, 'qas': [{'question': question, 'id': '0'}]}]

    model = QuestionAnsweringModel('albert', 'ahotrod/albert_xxlargev1_squad2_512',
                                    args={'max_seq_length': 512, "eval_batch_size": 3, "version_2_with_negative": True, 'reprocess_input_data': True, 'overwrite_output_dir': True})
    print(model.predict(to_predict)[0]['answer'])
