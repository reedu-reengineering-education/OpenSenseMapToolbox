FROM python:latest

WORKDIR atrai

COPY req.txt req.txt
RUN pip install -r req.txt

COPY ./opensensemaptoolbox ./opensensemaptoolbox
COPY setup.py setup.py
RUN pip install -e .

COPY . .

CMD [ "python", "main.py" ]
#CMD [ "sleep", "infinity" ]